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
        
        if not self.client:
            print(colored(f"Warning: {self.provider.upper()} client could not be initialized. Check your configuration.", "red"))
        
        print(colored(f"[{self._timestamp()}] Navigator Agent initialized with {self.provider.upper()}", "magenta"))
    
    def set_observer(self, observer):
        """Set reference to observer agent"""
        self.observer = observer
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file"""
        config_file = f"{self.provider}_config.toml"
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
        api_key = self.config.get('anthropic', {}).get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        
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
        config_section = self.config.get('openai', {})
        api_key = config_section.get('api_key') or os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print(colored("Warning: OPENAI_API_KEY not found in config or environment.", "red"))
            return None
        
        try:
            base_url = config_section.get('base_url')
            if base_url:
                return openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                return openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(colored(f"Error initializing OpenAI client: {e}", "red"))
            return None
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
    
    def process_changes(self, changes_summary: Dict[str, Any]):
        """Process file changes and generate proactive comments"""
        if not self.client:
            return
            
        try:
            # Create context about the changes
            context = self._build_change_context(changes_summary)
            
            # Generate response using Claude
            response = self._generate_response(context, is_proactive=True)
            
            if response:
                self._display_agent_comment(response)
                
        except Exception as e:
            print(colored(f"[{self._timestamp()}] Error processing changes: {e}", "red"))
    
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
    
    def _generate_response(self, context: str, is_proactive: bool = True) -> str:
        """Generate response using configured LLM provider"""
        if self.provider == "anthropic":
            return self._generate_anthropic_response(context, is_proactive)
        elif self.provider == "openai":
            return self._generate_openai_response(context, is_proactive)
        else:
            print(colored(f"[{self._timestamp()}] Unsupported provider: {self.provider}", "red"))
            return None
    
    def _generate_anthropic_response(self, context: str, is_proactive: bool = True) -> str:
        """Generate response using Anthropic Claude API"""
        try:
            # Get config values
            config_section = self.config.get('anthropic', {})
            model = config_section.get('model', 'claude-3-5-sonnet-20241022')
            max_tokens = config_section.get('max_tokens', 200)
            temperature = config_section.get('temperature', 0.7)
            
            # Build the system prompt
            system_prompt = self._get_system_prompt(is_proactive)
            
            # Build messages for the API call
            messages = self._build_messages(context, is_proactive)
            
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
    
    def _generate_openai_response(self, context: str, is_proactive: bool = True) -> str:
        """Generate response using OpenAI API"""
        try:
            # Get config values
            config_section = self.config.get('openai', {})
            model = config_section.get('model', 'gpt-4o')
            max_tokens = config_section.get('max_tokens', 200)
            temperature = config_section.get('temperature', 0.7)
            
            # Build the system prompt
            system_prompt = self._get_system_prompt(is_proactive)
            
            # Build messages for the API call
            messages = self._build_messages(context, is_proactive)
            
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
    
    def _build_messages(self, context: str, is_proactive: bool = True) -> List[Dict[str, str]]:
        """Build messages array for API call"""
        messages = []
        
        if is_proactive:
            # For proactive comments based on file changes
            messages.append({
                "role": "user",
                "content": f"Here are the recent code changes I've observed:\n\n{context}\n\nPlease provide a brief, conversational comment about these changes."
            })
        else:
            # For responding to user input
            # Include recent conversation history for context
            max_history = self.config.get(self.provider, {}).get('limits', {}).get('max_conversation_history', 6)
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
    
    def _get_system_prompt(self, is_proactive: bool) -> str:
        """Get the system prompt from config or use default"""
        config_section = self.config.get(self.provider, {})
        system_prompts = config_section.get('system_prompts', {})
        
        prompt_key = 'proactive' if is_proactive else 'interactive'
        
        # Return configured prompt or fallback to default
        return system_prompts.get(prompt_key, self._get_default_system_prompt(is_proactive))
    
    def _get_default_system_prompt(self, is_proactive: bool) -> str:
        """Get default system prompt as fallback"""
        if is_proactive:
            return """You are Blue, a helpful pair programming assistant observing code changes in real-time. 
            
Your role is to provide brief, conversational comments about code changes you observe, focusing on:
- Architecture and design patterns
- Potential improvements or considerations
- Code quality observations
- Security or performance implications

Keep your responses:
- Conversational and friendly (like talking to a colleague)
- Brief (1-2 sentences max)
- Focused on high-level insights, not low-level syntax
- Encouraging and constructive

Start responses naturally, as if you're commenting during a coding session. Examples:
- "Hey, nice addition of that auth function..."
- "I notice you're working on..."
- "That new component looks good, though..."

Avoid being overly formal or verbose."""

        else:
            return """You are Blue, a friendly pair programming assistant. You're having a real-time conversation with a developer while observing their code changes.

Respond naturally and conversationally, as if you're a colleague sitting next to them. Keep responses:
- Brief and to the point
- Helpful and constructive  
- Focused on their specific question or comment
- Encouraging

You can discuss code architecture, suggest improvements, answer questions, or just chat about the development process."""
    
    def _display_agent_comment(self, comment: str):
        """Display agent comment with color coding and timestamp"""
        timestamp = self._timestamp()
        
        # Format the comment with a conversational prefix
        formatted_comment = f"[{timestamp}] 🤖 {comment}"
        
        print(colored(formatted_comment, "green", attrs=['bold']))
        print()  # Add some spacing