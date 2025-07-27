"""
Navigator Agent

LLM-powered reasoning and conversation agent with dynamic decision making.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import autogen

from blue.agents.base import BaseAgent
from blue.core.llm_client import LLMClientFactory, LLMClient
from blue.core.decision_engine import DecisionEngine
from blue.core.feedback_system import FeedbackSystem
from blue.core.scoring import ScoringSystem


class NavigatorAgent(BaseAgent):
    """Navigator Agent - Handles LLM interactions and decision making"""
    
    def __init__(self, config: Dict[str, Any], provider: str = "anthropic"):
        super().__init__(config)
        self.provider = provider.lower()
        self.observer = None
        self.conversation_history = []
        
        # Initialize core components
        self.llm_client: Optional[LLMClient] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.feedback_system: Optional[FeedbackSystem] = None
        self.scoring_system: Optional[ScoringSystem] = None
        self.autogen_agents = {}
        
        self.initialize()
    
    def initialize(self):
        """Initialize the navigator agent"""
        try:
            # Initialize LLM client
            model_config = self.config.get('models', {}).get(self.provider, {})
            self.llm_client = LLMClientFactory.create_client(self.provider, model_config)
            
            if not self.llm_client or not self.llm_client.is_available():
                self._log_warning(f"{self.provider.upper()} client could not be initialized. Check your configuration.")
            else:
                self._log_success(f"Initialized with {self.provider.upper()}")
            
            # Initialize core systems
            self.decision_engine = DecisionEngine(self.llm_client, self.config)
            self.feedback_system = FeedbackSystem(self.config)
            self.scoring_system = ScoringSystem(self.config)
            
            # Initialize AutoGen agents
            self.autogen_agents = self._initialize_autogen_agents()
            
            self._initialized = True
            
        except Exception as e:
            self._log_error(f"Failed to initialize: {e}")
    
    def set_observer(self, observer):
        """Set reference to observer agent"""
        self.observer = observer
    
    def process_changes(self, changes_summary: Dict[str, Any]):
        """Process code changes and potentially generate comments"""
        if not self.llm_client or not self.llm_client.is_available():
            return
            
        try:
            # First: Basic scoring check
            should_comment = self._should_generate_comment(changes_summary)
            
            if not should_comment:
                return
            
            # Second: LLM-based dynamic decision (if enabled)
            changes_context = self._build_change_context(changes_summary)
            llm_decision = self.decision_engine.should_comment_via_llm(changes_summary, changes_context)
            
            if not llm_decision:
                self._log_debug("LLM decided not to comment")
                return
            
            # Generate response
            response = self._generate_response(changes_context, is_proactive=True, changes_summary=changes_summary)
            
            if response:
                self._display_agent_comment(response)
                
                # Add to conversation history
                comment_entry = {
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now(),
                    'type': 'proactive',
                    'reason': changes_summary.get('processing_reason', 'unknown'),
                    'score': changes_summary.get('buffer_score', 0)
                }
                self.conversation_history.append(comment_entry)
                
                # Mark for feedback
                self.feedback_system.mark_awaiting_feedback(comment_entry)
                
        except Exception as e:
            self._log_error(f"Error processing changes: {e}")
    
    def handle_user_input(self, user_input: str):
        """Handle user input and generate conversational response"""
        if not self.llm_client or not self.llm_client.is_available():
            self._log_error("Cannot respond - LLM client not available")
            return
            
        try:
            # Check if this is feedback on our last comment
            feedback_processed = self.feedback_system.process_potential_feedback(
                user_input, self.conversation_history
            )
            
            # Add user input to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now(),
                'is_feedback': feedback_processed
            })
            
            # Generate response (skip if it was just feedback)
            if not feedback_processed:
                response = self._generate_response(user_input, is_proactive=False)
                
                if response:
                    self._display_agent_comment(response)
                    # Add response to conversation history
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now()
                    })
                
        except Exception as e:
            self._log_error(f"Error handling user input: {e}")
    
    def _should_generate_comment(self, changes_summary: Dict[str, Any]) -> bool:
        """Determine if we should generate a comment based on scoring"""
        priority = changes_summary.get('priority_level', 'low')
        reason = changes_summary.get('processing_reason', 'unknown')
        buffer_score = changes_summary.get('buffer_score', 0)
        
        # Use adaptive threshold from feedback system
        score_threshold = self.feedback_system.get_current_threshold()
        
        # Primary decision: Score-based with adaptive threshold
        if reason == 'score_threshold' and buffer_score >= score_threshold:
            self._log_debug(f"Score {buffer_score} >= adaptive threshold {score_threshold}")
            return True
            
        # High priority changes with slightly lower threshold
        if priority == 'high' and buffer_score >= max(score_threshold - 2, 3):
            return True
            
        # Function completion with lower threshold
        if reason == 'function_completion' and buffer_score >= max(score_threshold - 1, 3):
            return True
            
        # Architectural changes
        if reason == 'architectural_change' and buffer_score >= max(score_threshold - 1, 3):
            return True
            
        # Idle timeout with minimum score
        if reason == 'idle_timeout' and buffer_score >= max(score_threshold - 2, 2):
            return True
            
        # Medium priority with adaptive threshold
        if priority == 'medium' and buffer_score >= score_threshold:
            recent_comments = [h for h in self.conversation_history[-3:] if h.get('type') == 'proactive']
            return len(recent_comments) <= 1
            
        # Low priority needs higher score
        if priority == 'low' and buffer_score >= score_threshold + 2:
            files_affected = changes_summary.get('files_affected', 0)
            return files_affected >= 2
            
        return False
    
    def _build_change_context(self, changes_summary: Dict[str, Any]) -> str:
        """Build context string from changes summary"""
        context_parts = []
        
        context_parts.append(f"I've observed {changes_summary['total_changes']} recent changes across {changes_summary['files_affected']} files:")
        
        max_changes = self.config.get('limits', {}).get('max_recent_changes', 5)
        
        for change in changes_summary['changes'][-max_changes:]:
            file_info = f"- {change['file']} ({change['type']})"
            
            if 'lines_changed' in change['details']:
                file_info += f": {change['details']['lines_changed']}"
            
            if 'functions_added' in change['details'] and change['details']['functions_added']:
                func_names = ', '.join(change['details']['functions_added'])
                file_info += f", new functions: {func_names}"
            
            context_parts.append(file_info)
        
        return '\\n'.join(context_parts)
    
    def _generate_response(self, context: str, is_proactive: bool = True, changes_summary: Dict[str, Any] = None) -> Optional[str]:
        """Generate response using LLM client"""
        if not self.llm_client:
            return None
        
        try:
            # Build system prompt
            system_prompt = self._get_system_prompt(is_proactive, changes_summary)
            
            # Build messages
            messages = self._build_messages(context, is_proactive, changes_summary)
            
            # Generate response
            response = self.llm_client.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            return response
            
        except Exception as e:
            self._log_error(f"LLM API error: {e}")
            return None
    
    def _build_messages(self, context: str, is_proactive: bool = True, changes_summary: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Build messages array for API call"""
        messages = []
        
        if is_proactive:
            # Enhanced proactive prompting
            priority = changes_summary.get('priority_level', 'low') if changes_summary else 'low'
            reason = changes_summary.get('processing_reason', 'unknown') if changes_summary else 'unknown'
            
            prompt = self._build_contextual_prompt(context, priority, reason)
            messages.append({"role": "user", "content": prompt})
        else:
            # Include conversation history for context
            max_history = self.config.get('limits', {}).get('max_conversation_history', 8)
            recent_history = self.conversation_history[-max_history:]
            
            if recent_history:
                history_context = "Recent conversation:\\n"
                for entry in recent_history:
                    role = "You" if entry['role'] == 'assistant' else "Developer"
                    history_context += f"{role}: {entry['content']}\\n"
                
                messages.append({
                    "role": "user", 
                    "content": f"{history_context}\\nDeveloper: {context}"
                })
            else:
                messages.append({"role": "user", "content": context})
        
        return messages
    
    def _build_contextual_prompt(self, context: str, priority: str, reason: str) -> str:
        """Build contextually aware prompt"""
        base_prompt = f"Here are the recent code changes I've observed:\\n\\n{context}\\n\\n"
        
        if reason == 'function_completion':
            return base_prompt + "I detected a new function was added. Please provide a brief, encouraging comment about the function and any architectural considerations."
        elif reason == 'architectural_change':
            return base_prompt + "I detected structural changes (new files, imports, etc.). Please comment on the architectural implications."
        elif reason == 'sustained_activity':
            return base_prompt + "I see sustained development activity across multiple files. Please provide a big-picture observation about the current development direction."
        elif priority == 'high':
            return base_prompt + "These changes seem significant. Please provide thoughtful commentary on their implications."
        else:
            return base_prompt + "Please provide a brief, casual comment about these changes like a human navigator would."
    
    def _get_system_prompt(self, is_proactive: bool, changes_summary: Dict[str, Any] = None) -> str:
        """Get system prompt with contextual awareness"""
        system_prompts = self.config.get('system_prompts', {})
        prompt_key = 'proactive' if is_proactive else 'interactive'
        
        base_prompt = system_prompts.get(prompt_key, self._get_default_system_prompt(is_proactive))
        
        if is_proactive and changes_summary:
            priority = changes_summary.get('priority_level', 'low')
            reason = changes_summary.get('processing_reason', 'unknown')
            
            # Add contextual guidance
            context_addition = ""
            if reason == 'function_completion':
                context_addition = "\\n\\nFocus on: function design, testing considerations, and integration points."
            elif reason == 'architectural_change':
                context_addition = "\\n\\nFocus on: system design, module interactions, and maintainability."
            elif reason == 'sustained_activity':
                context_addition = "\\n\\nFocus on: development velocity, code organization, and emerging patterns."
            elif priority == 'high':
                context_addition = "\\n\\nFocus on: security, performance, and best practices."
                
            return base_prompt + context_addition
            
        return base_prompt
    
    def _get_default_system_prompt(self, is_proactive: bool) -> str:
        """Get default system prompt if config is missing"""
        if is_proactive:
            return "You are Blue, an ambient pair programming assistant. Provide brief, helpful comments about code changes you observe."
        else:
            return "You are Blue, a friendly coding assistant. Help the developer with their questions and provide conversational support."
    
    def _display_agent_comment(self, comment: str):
        """Display agent comment with formatting"""
        timestamp = self._timestamp()
        formatted_comment = f"[{timestamp}] 🤖 {comment}"
        self._log_success(formatted_comment)
        print()  # Add spacing
    
    def _initialize_autogen_agents(self) -> Dict[str, Any]:
        """Initialize AutoGen agents if possible"""
        try:
            config_list = self._get_autogen_config()
            if not config_list:
                return {}
            
            system_prompts = self.config.get('system_prompts', {})
            
            # Create specialized agents
            agents = {}
            
            # Code reviewer agent
            if 'code_reviewer' in system_prompts:
                agents['code_reviewer'] = autogen.AssistantAgent(
                    name="code_reviewer",
                    system_message=system_prompts['code_reviewer'],
                    llm_config={"config_list": config_list}
                )
            
            # Architect agent
            if 'architect' in system_prompts:
                agents['architect'] = autogen.AssistantAgent(
                    name="architect",
                    system_message=system_prompts['architect'],
                    llm_config={"config_list": config_list}
                )
            
            # User proxy for coordination
            agents['user_proxy'] = autogen.UserProxyAgent(
                name="navigator_proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1,
                code_execution_config=False
            )
            
            self._log_success("AutoGen agents initialized")
            return agents
            
        except Exception as e:
            self._log_warning(f"Could not initialize AutoGen agents: {e}")
            return {}
    
    def _get_autogen_config(self) -> List[Dict[str, Any]]:
        """Get AutoGen configuration"""
        config_list = []
        
        if self.provider == "anthropic":
            model_config = self.config.get('models', {}).get('anthropic', {})
            api_key = model_config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                config_list.append({
                    "model": model_config.get('model', 'claude-3-5-sonnet-20241022'),
                    "api_key": api_key,
                    "api_type": "anthropic"
                })
        elif self.provider == "openai":
            model_config = self.config.get('models', {}).get('openai', {})
            api_key = model_config.get('api_key') or os.getenv('OPENAI_API_KEY')
            if api_key:
                config_list.append({
                    "model": model_config.get('model', 'gpt-4o'),
                    "api_key": api_key,
                    "api_type": "openai"
                })
        
        return config_list
    
    def get_status(self) -> Dict[str, Any]:
        """Get navigator agent status"""
        base_status = super().get_status()
        base_status.update({
            'provider': self.provider,
            'llm_available': self.llm_client.is_available() if self.llm_client else False,
            'conversation_entries': len(self.conversation_history),
            'autogen_agents': list(self.autogen_agents.keys()),
            'current_threshold': self.feedback_system.get_current_threshold() if self.feedback_system else None,
            'feedback_stats': self.feedback_system.get_feedback_stats() if self.feedback_system else None
        })
        return base_status