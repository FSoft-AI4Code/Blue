"""
Chat Manager

Manages the conversational interface between user and NavigatorAgent.
Handles message formatting, conversation flow, and user input processing.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from termcolor import colored

from .history_manager import HistoryManager
from .feedback_processor import FeedbackProcessor


class ChatManager:
    """Manages chat interactions between user and NavigatorAgent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.history_manager = HistoryManager(config)
        self.feedback_processor = FeedbackProcessor(config)
        
        # Chat state
        self.active_session = True
        self.last_message_timestamp = None
    
    def process_user_input(self, user_input: str, navigator_agent) -> bool:
        """Process user input and coordinate response. Returns True if input was processed."""
        if not user_input.strip():
            return False
        
        self.last_message_timestamp = datetime.now()
        
        # Check if this is feedback on the last assistant message
        feedback_processed = self.feedback_processor.process_potential_feedback(
            user_input, 
            self.history_manager.get_conversation_history()
        )
        
        # Add user input to history
        self.history_manager.add_user_message(user_input, is_feedback=feedback_processed)
        
        # If it was just feedback, don't need to generate a response
        if feedback_processed:
            return True
        
        # Generate response from NavigatorAgent
        try:
            response = navigator_agent.generate_conversational_response(user_input, self.get_conversation_context())
            
            if response:
                self.display_assistant_message(response)
                self.history_manager.add_assistant_message(response, message_type='conversational')
                
                # Mark message as awaiting potential feedback
                self.feedback_processor.mark_awaiting_feedback(
                    self.history_manager.get_last_assistant_message()
                )
                
            return True
            
        except Exception as e:
            self.display_error(f"Error generating response: {e}")
            return False
    
    def handle_proactive_comment(self, comment: str, changes_summary: Dict[str, Any]):
        """Handle a proactive comment from NavigatorAgent"""
        timestamp = datetime.now()
        
        # Display the comment
        self.display_assistant_message(comment, is_proactive=True)
        
        # Add to history with metadata
        self.history_manager.add_assistant_message(
            comment, 
            message_type='proactive',
            metadata={
                'reason': changes_summary.get('processing_reason', 'unknown'),
                'score': changes_summary.get('buffer_score', 0),
                'priority': changes_summary.get('priority_level', 'low'),
                'files_affected': changes_summary.get('files_affected', 0)
            }
        )
        
        # Mark as awaiting feedback
        self.feedback_processor.mark_awaiting_feedback(
            self.history_manager.get_last_assistant_message()
        )
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get context for NavigatorAgent response generation"""
        history = self.history_manager.get_recent_history()
        feedback_stats = self.feedback_processor.get_feedback_stats()
        
        return {
            'recent_history': history,
            'conversation_length': len(self.history_manager.get_conversation_history()),
            'feedback_stats': feedback_stats,
            'session_active': self.active_session,
            'last_message_time': self.last_message_timestamp.isoformat() if self.last_message_timestamp else None
        }
    
    def display_assistant_message(self, message: str, is_proactive: bool = False):
        """Display assistant message with appropriate formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if is_proactive:
            # Proactive comments get special formatting
            formatted_message = f"[{timestamp}] 🤖 {message}"
            print(colored(formatted_message, "green", attrs=['bold']))
        else:
            # Conversational responses are more casual
            formatted_message = f"[{timestamp}] Blue: {message}"
            print(colored(formatted_message, "cyan"))
        
        print()  # Add spacing
    
    def display_error(self, error_message: str):
        """Display error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] Error: {error_message}"
        print(colored(formatted_message, "red"))
    
    def display_system_message(self, message: str):
        """Display system message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] System: {message}"
        print(colored(formatted_message, "yellow"))
    
    def get_feedback_processor(self) -> FeedbackProcessor:
        """Get the feedback processor for external access"""
        return self.feedback_processor
    
    def get_history_manager(self) -> HistoryManager:
        """Get the history manager for external access"""
        return self.history_manager
    
    def start_session(self):
        """Start a new chat session"""
        self.active_session = True
        self.display_system_message("Chat session started")
    
    def end_session(self):
        """End the current chat session"""
        self.active_session = False
        
        # Display session summary
        stats = self.get_session_stats()
        if stats['total_messages'] > 0:
            print()
            print(colored("📊 CHAT SESSION SUMMARY", "cyan", attrs=['bold']))
            print(colored("-" * 30, "cyan"))
            print(colored(f"Total messages: {stats['total_messages']}", "white"))
            print(colored(f"User messages: {stats['user_messages']}", "white"))
            print(colored(f"Assistant messages: {stats['assistant_messages']}", "white"))
            print(colored(f"Proactive comments: {stats['proactive_comments']}", "white"))
            
            feedback_stats = self.feedback_processor.get_feedback_stats()
            if feedback_stats['total_feedback'] > 0:
                print(colored(f"Feedback received: {feedback_stats['total_feedback']}", "white"))
                print(colored(f"  Positive: {feedback_stats['positive_feedback']}", "green"))
                print(colored(f"  Negative: {feedback_stats['negative_feedback']}", "red"))
        
        self.display_system_message("Chat session ended")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current session"""
        history = self.history_manager.get_conversation_history()
        
        user_messages = sum(1 for msg in history if msg.get('role') == 'user')
        assistant_messages = sum(1 for msg in history if msg.get('role') == 'assistant')
        proactive_comments = sum(1 for msg in history if msg.get('role') == 'assistant' and msg.get('type') == 'proactive')
        
        return {
            'total_messages': len(history),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'proactive_comments': proactive_comments,
            'session_active': self.active_session,
            'session_duration': (datetime.now() - self.history_manager.session_start_time).total_seconds() if hasattr(self.history_manager, 'session_start_time') else 0
        }
    
    def clear_conversation(self):
        """Clear the conversation history"""
        self.history_manager.clear_history()
        self.feedback_processor.clear_feedback_history()
        self.display_system_message("Conversation history cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get chat manager status"""
        return {
            'name': 'ChatManager',
            'session_active': self.active_session,
            'last_message_time': self.last_message_timestamp.isoformat() if self.last_message_timestamp else None,
            'session_stats': self.get_session_stats(),
            'feedback_stats': self.feedback_processor.get_feedback_stats()
        }