"""
Navigator Agent - LLM-powered reasoning and conversation
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from termcolor import colored
import anthropic
import openai
import toml
import autogen
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NavigatorAgent:
    def __init__(self, provider: str = "anthropic"):
        self.observer = None
        self.conversation_history = []
        self.provider = provider.lower()
        self.config = self._load_config()
        self.client = self._initialize_client()
        
        # Initialize AutoGen agents for enhanced coordination
        self.autogen_agents = self._initialize_autogen_agents()
        
        if not self.client:
            print(colored(f"Warning: {self.provider.upper()} client could not be initialized. Check your configuration.", "red"))
        
        print(colored(f"[{self._timestamp()}] Navigator Agent initialized with {self.provider.upper()}", "magenta"))
    
    def set_observer(self, observer):
        """Set reference to observer agent"""
        self.observer = observer
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from unified config.toml file"""
        config_file = "config.toml"
        try:
            with open(config_file, 'r') as f:
                return toml.load(f)
        except FileNotFoundError:
            print(colored(f"Warning: {config_file} not found. Using default settings.", "yellow"))
            return {}
        except Exception as e:
            print(colored(f"Error loading {config_file}: {e}", "red"))
            return {}
    
    def _initialize_client(self) -> Optional[Any]:
        """Initialize the appropriate LLM client"""
        if self.provider == "anthropic":
            return self._initialize_anthropic_client()
        elif self.provider == "openai":
            return self._initialize_openai_client()
        else:
            print(colored(f"Unsupported provider: {self.provider}", "red"))
            return None
    
    def _initialize_anthropic_client(self) -> Optional[anthropic.Anthropic]:
        """Initialize Anthropic Claude client"""
        # Try to get API key from config first, then environment
        model_config = self.config.get('models', {}).get('anthropic', {})
        api_key = model_config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            print(colored("Warning: ANTHROPIC_API_KEY not found in config or environment.", "red"))
            return None
        
        try:
            return anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            print(colored(f"Error initializing Anthropic client: {e}", "red"))
            return None
    
    def _initialize_openai_client(self) -> Optional[openai.OpenAI]:
        """Initialize OpenAI client"""
        # Try to get API key from config first, then environment
        model_config = self.config.get('models', {}).get('openai', {})
        api_key = model_config.get('api_key') or os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print(colored("Warning: OPENAI_API_KEY not found in config or environment.", "red"))
            return None
        
        try:
            base_url = model_config.get('base_url')
            if base_url:
                return openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                return openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(colored(f"Error initializing OpenAI client: {e}", "red"))
            return None
    
    def _initialize_autogen_agents(self) -> Dict[str, Any]:
        """Initialize AutoGen agents for enhanced coordination"""
        try:
            # Configuration for AutoGen agents
            config_list = self._get_autogen_config()
            
            if not config_list:
                return {}
            
            # Get system prompts from config
            system_prompts = self.config.get('system_prompts', {})
            
            # Create a code reviewer agent
            code_reviewer_prompt = system_prompts.get('code_reviewer', 
                "You are an expert code reviewer focusing on security, performance, and code quality.")
            code_reviewer = autogen.AssistantAgent(
                name="code_reviewer",
                system_message=code_reviewer_prompt,
                llm_config={"config_list": config_list}
            )
            
            # Create an architect agent
            architect_prompt = system_prompts.get('architect',
                "You are a software architect focusing on system design and scalability.")
            architect = autogen.AssistantAgent(
                name="architect",
                system_message=architect_prompt,
                llm_config={"config_list": config_list}
            )
            
            # Create a user proxy for coordination
            user_proxy = autogen.UserProxyAgent(
                name="navigator_proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1,
                code_execution_config=False
            )
            
            return {
                "code_reviewer": code_reviewer,
                "architect": architect,
                "user_proxy": user_proxy
            }
            
        except Exception as e:
            print(colored(f"Warning: Could not initialize AutoGen agents: {e}", "yellow"))
            return {}
    
    def _get_autogen_config(self) -> List[Dict[str, Any]]:
        """Get AutoGen configuration based on provider"""
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

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
    
    def process_changes(self, changes_summary: Dict[str, Any]):
        """Enhanced change processing with intelligent decision-making"""
        if not self.client:
            return
            
        try:
            # Decide if we should comment based on the changes
            should_comment = self._should_generate_comment(changes_summary)
            
            if not should_comment:
                return
            
            # Create context about the changes
            context = self._build_change_context(changes_summary)
            
            # Generate response with enhanced prompting
            response = self._generate_response(context, is_proactive=True, changes_summary=changes_summary)
            
            if response:
                self._display_agent_comment(response)
                # Add to conversation history for context
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now(),
                    'type': 'proactive',
                    'reason': changes_summary.get('processing_reason', 'unknown')
                })
                
        except Exception as e:
            print(colored(f"[{self._timestamp()}] Error processing changes: {e}", "red"))
    
    def _should_generate_comment(self, changes_summary: Dict[str, Any]) -> bool:
        """Intelligent decision on whether to generate a comment"""
        priority = changes_summary.get('priority_level', 'low')
        reason = changes_summary.get('processing_reason', 'unknown')
        total_changes = changes_summary.get('total_changes', 0)
        
        # Always comment on high priority changes
        if priority == 'high':
            return True
            
        # Comment on function completion regardless of priority
        if reason == 'function_completion':
            return True
            
        # Comment on architectural changes
        if reason == 'architectural_change':
            return True
            
        # For medium priority, comment sometimes (avoid spam)
        if priority == 'medium' and total_changes >= 3:
            # Check if we haven't commented recently
            recent_comments = [h for h in self.conversation_history[-3:] if h.get('type') == 'proactive']
            return len(recent_comments) <= 1
            
        # For low priority, rarely comment unless significant
        if priority == 'low' and total_changes >= 5:
            # Only if we have multiple files affected
            files_affected = changes_summary.get('files_affected', 0)
            return files_affected >= 2
            
        return False
    
    def handle_user_input(self, user_input: str):
        """Handle user input and generate conversational response"""
        if not self.client:
            print(colored(f"[{self._timestamp()}] Cannot respond - Claude API not configured", "red"))
            return
            
        try:
            # Add user input to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now()
            })
            
            # Generate response
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
            print(colored(f"[{self._timestamp()}] Error handling user input: {e}", "red"))
    
    def _build_change_context(self, changes_summary: Dict[str, Any]) -> str:
        """Build context string from changes summary"""
        context_parts = []
        
        context_parts.append(f"I've observed {changes_summary['total_changes']} recent changes across {changes_summary['files_affected']} files:")
        
        # Get max recent changes from config
        max_changes = self.config.get(self.provider, {}).get('limits', {}).get('max_recent_changes', 5)
        
        for change in changes_summary['changes'][-max_changes:]:
            file_info = f"- {change['file']} ({change['type']})"
            
            if 'lines_changed' in change['details']:
                file_info += f": {change['details']['lines_changed']}"
            
            if 'functions_added' in change['details'] and change['details']['functions_added']:
                func_names = ', '.join(change['details']['functions_added'])
                file_info += f", new functions: {func_names}"
            
            context_parts.append(file_info)
        
        return '\n'.join(context_parts)
    
    def _generate_response(self, context: str, is_proactive: bool = True, changes_summary: Dict[str, Any] = None) -> str:
        """Generate response using configured LLM provider with enhanced context"""
        if self.provider == "anthropic":
            return self._generate_anthropic_response(context, is_proactive, changes_summary)
        elif self.provider == "openai":
            return self._generate_openai_response(context, is_proactive, changes_summary)
        else:
            print(colored(f"[{self._timestamp()}] Unsupported provider: {self.provider}", "red"))
            return None
    
    def _generate_anthropic_response(self, context: str, is_proactive: bool = True, changes_summary: Dict[str, Any] = None) -> str:
        """Generate response using Anthropic Claude API with enhanced prompting"""
        try:
            # Get config values from unified config
            model_config = self.config.get('models', {}).get('anthropic', {})
            model = model_config.get('model', 'claude-3-5-sonnet-20241022')
            max_tokens = model_config.get('max_tokens', 250)
            temperature = model_config.get('temperature', 0.7)
            
            # Build the system prompt with context
            system_prompt = self._get_enhanced_system_prompt(is_proactive, changes_summary)
            
            # Build messages for the API call
            messages = self._build_messages(context, is_proactive, changes_summary)
            
            # Call Claude API
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(colored(f"[{self._timestamp()}] Anthropic API error: {e}", "red"))
            return None
    
    def _generate_openai_response(self, context: str, is_proactive: bool = True, changes_summary: Dict[str, Any] = None) -> str:
        """Generate response using OpenAI API with enhanced prompting"""
        try:
            # Get config values from unified config
            model_config = self.config.get('models', {}).get('openai', {})
            model = model_config.get('model', 'gpt-4o')
            max_tokens = model_config.get('max_tokens', 250)
            temperature = model_config.get('temperature', 0.7)
            
            # Build the system prompt with context
            system_prompt = self._get_enhanced_system_prompt(is_proactive, changes_summary)
            
            # Build messages for the API call
            messages = self._build_messages(context, is_proactive, changes_summary)
            
            # Add system message to the beginning for OpenAI
            messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(colored(f"[{self._timestamp()}] OpenAI API error: {e}", "red"))
            return None
    
    def _build_messages(self, context: str, is_proactive: bool = True, changes_summary: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Build messages array for API call with enhanced context"""
        messages = []
        
        if is_proactive:
            # Enhanced proactive prompting based on change analysis
            priority = changes_summary.get('priority_level', 'low') if changes_summary else 'low'
            reason = changes_summary.get('processing_reason', 'unknown') if changes_summary else 'unknown'
            
            prompt = self._build_contextual_prompt(context, priority, reason)
            messages.append({
                "role": "user",
                "content": prompt
            })
        else:
            # For responding to user input
            # Include recent conversation history for context
            max_history = self.config.get('limits', {}).get('max_conversation_history', 8)
            recent_history = self.conversation_history[-max_history:]
            
            if recent_history:
                history_context = "Recent conversation:\n"
                for entry in recent_history:
                    role = "You" if entry['role'] == 'assistant' else "Developer"
                    history_context += f"{role}: {entry['content']}\n"
                
                messages.append({
                    "role": "user", 
                    "content": f"{history_context}\nDeveloper: {context}"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": context
                })
        
        return messages
    
    def _build_contextual_prompt(self, context: str, priority: str, reason: str) -> str:
        """Build contextually aware prompt based on change analysis"""
        base_prompt = f"Here are the recent code changes I've observed:\n\n{context}\n\n"
        
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
    
    def _get_enhanced_system_prompt(self, is_proactive: bool, changes_summary: Dict[str, Any] = None) -> str:
        """Get enhanced system prompt with contextual awareness"""
        base_prompt = self._get_system_prompt(is_proactive)
        
        if is_proactive and changes_summary:
            priority = changes_summary.get('priority_level', 'low')
            reason = changes_summary.get('processing_reason', 'unknown')
            
            # Add contextual guidance based on the processing reason
            context_addition = ""
            if reason == 'function_completion':
                context_addition = "\n\nFocus on: function design, testing considerations, and integration points."
            elif reason == 'architectural_change':
                context_addition = "\n\nFocus on: system design, module interactions, and maintainability."
            elif reason == 'sustained_activity':
                context_addition = "\n\nFocus on: development velocity, code organization, and emerging patterns."
            elif priority == 'high':
                context_addition = "\n\nFocus on: security, performance, and best practices."
                
            return base_prompt + context_addition
            
        return base_prompt
    
    def _get_system_prompt(self, is_proactive: bool) -> str:
        """Get the system prompt from unified config"""
        system_prompts = self.config.get('system_prompts', {})
        prompt_key = 'proactive' if is_proactive else 'interactive'
        
        # Return configured prompt or fallback to default
        configured_prompt = system_prompts.get(prompt_key)
        if configured_prompt:
            return configured_prompt
        else:
            print(colored(f"Warning: No {prompt_key} system prompt found in config, using fallback", "yellow"))
            return self._get_default_system_prompt(is_proactive)
    
    def _get_default_system_prompt(self, is_proactive: bool) -> str:
        """Get minimal fallback system prompt if config is completely missing"""
        if is_proactive:
            return "You are Blue, an ambient pair programming assistant. Provide brief, helpful comments about code changes you observe."
        else:
            return "You are Blue, a friendly coding assistant. Help the developer with their questions and provide conversational support."
    
    def _display_agent_comment(self, comment: str):
        """Display agent comment with color coding and timestamp"""
        timestamp = self._timestamp()
        
        # Format the comment with a conversational prefix
        formatted_comment = f"[{timestamp}] 🤖 {comment}"
        
        print(colored(formatted_comment, "green", attrs=['bold']))
        print()  # Add some spacing