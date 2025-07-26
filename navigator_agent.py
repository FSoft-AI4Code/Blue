"""
Navigator Agent - LLM-powered reasoning and conversation
"""

import os
from datetime import datetime
from typing import Dict, Any, List
from termcolor import colored
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NavigatorAgent:
    def __init__(self):
        self.observer = None
        self.conversation_history = []
        
        # Initialize Claude client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print(colored("Warning: ANTHROPIC_API_KEY not found in environment. Please set it to use Claude.", "red"))
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        
        print(colored(f"[{self._timestamp()}] Navigator Agent initialized", "magenta"))
    
    def set_observer(self, observer):
        """Set reference to observer agent"""
        self.observer = observer
    
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
        
        for change in changes_summary['changes'][-5:]:  # Last 5 changes
            file_info = f"- {change['file']} ({change['type']})"
            
            if 'lines_changed' in change['details']:
                file_info += f": {change['details']['lines_changed']}"
            
            if 'functions_added' in change['details'] and change['details']['functions_added']:
                func_names = ', '.join(change['details']['functions_added'])
                file_info += f", new functions: {func_names}"
            
            context_parts.append(file_info)
        
        return '\n'.join(context_parts)
    
    def _generate_response(self, context: str, is_proactive: bool = True) -> str:
        """Generate response using Claude API"""
        try:
            # Build the system prompt
            system_prompt = self._get_system_prompt(is_proactive)
            
            # Build messages for the API call
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
                recent_history = self.conversation_history[-6:]  # Last 3 exchanges
                
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
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,  # Keep responses concise
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(colored(f"[{self._timestamp()}] Claude API error: {e}", "red"))
            return None
    
    def _get_system_prompt(self, is_proactive: bool) -> str:
        """Get the system prompt for Claude"""
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