"""
Navigator Agent

The main LLM-powered agent that provides coding insights and conversational support.
This is the "thinking" agent that generates responses and provides programming assistance.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseAgent
from blue.core.llm_client import LLMClient
from blue.core.llm_config import LLMConfigManager
from blue.conversation.chat_manager import ChatManager
from .intervention_agent import InterventionAgent


class NavigatorAgent(BaseAgent):
    """Main LLM-powered agent for providing coding insights and conversation"""
    
    def __init__(self, config: Dict[str, Any], provider: str = "anthropic"):
        super().__init__(config)
        self.provider = provider.lower()  # Keep for backward compatibility
        
        # Core components
        self.llm_config_manager = LLMConfigManager(config)
        self.llm_client: Optional[LLMClient] = None
        self.intervention_agent: Optional[InterventionAgent] = None
        self.chat_manager: Optional[ChatManager] = None
        
        # Monitor reference (set externally)
        self.codebase_monitor = None
        
        self.initialize()
    
    def initialize(self):
        """Initialize the navigator agent"""
        try:
            # Initialize LLM client using agent-specific configuration
            self.llm_client = self.llm_config_manager.create_client_for_agent('navigator')
            
            if not self.llm_client or not self.llm_client.is_available():
                agent_info = self.llm_config_manager.get_agent_info('navigator')
                self._log_warning(f"NavigatorAgent LLM client ({agent_info['provider'].upper()}) could not be initialized. Check your configuration.")
            else:
                agent_info = self.llm_config_manager.get_agent_info('navigator')
                self._log_success(f"Initialized with {agent_info['provider'].upper()} using {agent_info['model']}")
            
            # Initialize intervention agent with its own LLM configuration
            self.intervention_agent = InterventionAgent(self.config, self.llm_config_manager)
            self.intervention_agent.initialize()
            
            # Initialize chat manager
            self.chat_manager = ChatManager(self.config)
            
            self._initialized = True
            
        except Exception as e:
            self._log_error(f"Failed to initialize: {e}")
    
    def set_codebase_monitor(self, monitor):
        """Set reference to codebase monitor"""
        self.codebase_monitor = monitor
    
    def process_code_changes(self, changes_summary: Dict[str, Any]):
        """Process code changes and potentially generate proactive comments"""
        if not self.llm_client or not self.llm_client.is_available():
            self._log_warning("Cannot process changes - LLM client not available")
            return
            
        try:
            # First: Check if we should intervene
            changes_context = self._build_change_context(changes_summary)
            
            should_intervene = self.intervention_agent.should_intervene(changes_summary, changes_context)
            
            if not should_intervene:
                self._log_debug("InterventionAgent decided not to intervene")
                return
            
            # Generate proactive comment
            response = self._generate_proactive_response(changes_context, changes_summary)
            
            if response:
                # Use chat manager to handle the proactive comment
                self.chat_manager.handle_proactive_comment(response, changes_summary)
                
        except Exception as e:
            self._log_error(f"Error processing code changes: {e}")
    
    def handle_user_input(self, user_input: str):
        """Handle user input through chat manager"""
        if not self.llm_client or not self.llm_client.is_available():
            self._log_error("Cannot respond - LLM client not available")
            return
        
        try:
            self.chat_manager.process_user_input(user_input, self)
        except Exception as e:
            self._log_error(f"Error handling user input: {e}")
    
    def generate_conversational_response(self, user_input: str, context: Dict[str, Any]) -> Optional[str]:
        """Generate a conversational response to user input"""
        try:
            # Build system prompt for conversation
            system_prompt = self._get_system_prompt(is_proactive=False)
            
            # Build messages with context
            messages = self._build_conversational_messages(user_input, context)
            
            # Generate response
            response = self.llm_client.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            return response
            
        except Exception as e:
            self._log_error(f"Error generating conversational response: {e}")
            return None
    
    def _generate_proactive_response(self, changes_context: str, changes_summary: Dict[str, Any]) -> Optional[str]:
        """Generate a proactive response about code changes"""
        try:
            # Build system prompt for proactive comments
            system_prompt = self._get_system_prompt(is_proactive=True, changes_summary=changes_summary)
            
            # Build contextual prompt
            priority = changes_summary.get('priority_level', 'low')
            reason = changes_summary.get('processing_reason', 'unknown')
            prompt = self._build_contextual_prompt(changes_context, priority, reason)
            
            messages = [{"role": "user", "content": prompt}]
            
            # Generate response
            response = self.llm_client.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            return response
            
        except Exception as e:
            self._log_error(f"Error generating proactive response: {e}")
            return None
    
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
    
    def _build_conversational_messages(self, user_input: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build messages for conversational response"""
        messages = []
        
        # Include recent conversation history if available
        recent_history = context.get('recent_history', [])
        if recent_history:
            # Convert to LLM format
            for msg in recent_history[-6:]:  # Last 6 messages for context
                if not msg.get('is_feedback', False):  # Skip feedback messages
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        return messages
    
    def _build_contextual_prompt(self, context: str, priority: str, reason: str) -> str:
        """Build contextually aware prompt based on change analysis"""
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
            return base_prompt + "Please provide a brief, casual comment about these changes like a helpful pair programming partner would."
    
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
    
    def get_chat_manager(self) -> Optional[ChatManager]:
        """Get the chat manager for external access"""
        return self.chat_manager
    
    def get_intervention_agent(self) -> Optional[InterventionAgent]:
        """Get the intervention agent for external access"""
        return self.intervention_agent
    
    def get_status(self) -> Dict[str, Any]:
        """Get navigator agent status"""
        base_status = super().get_status()
        
        # Get agent-specific LLM configuration info
        navigator_info = self.llm_config_manager.get_agent_info('navigator')
        
        # Get current threshold from chat manager's feedback processor
        current_threshold = None
        feedback_stats = None
        if self.chat_manager and self.chat_manager.get_feedback_processor():
            current_threshold = self.chat_manager.get_feedback_processor().get_current_threshold()
            feedback_stats = self.chat_manager.get_feedback_processor().get_feedback_stats()
        
        base_status.update({
            'provider': navigator_info['provider'],
            'model': navigator_info['model'],
            'llm_available': self.llm_client.is_available() if self.llm_client else False,
            'current_threshold': current_threshold,
            'feedback_stats': feedback_stats,
            'intervention_agent_status': self.intervention_agent.get_status() if self.intervention_agent else None,
            'chat_manager_status': self.chat_manager.get_status() if self.chat_manager else None,
            'llm_config_validation': self.llm_config_manager.validate_configuration()
        })
        return base_status