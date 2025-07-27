"""
History Manager

Manages conversation history, message storage, and context retrieval.
Provides clean interfaces for adding messages and retrieving conversation context.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class HistoryManager:
    """Manages conversation history and message context"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.limits = config.get('limits', {})
        
        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_start_time = datetime.now()
        self.max_history_size = self.limits.get('max_conversation_history', 50)
    
    def add_user_message(self, content: str, is_feedback: bool = False, metadata: Dict[str, Any] = None):
        """Add a user message to the conversation history"""
        message = {
            'role': 'user',
            'content': content,
            'timestamp': datetime.now(),
            'is_feedback': is_feedback,
            'metadata': metadata or {}
        }
        
        self._add_message(message)
    
    def add_assistant_message(self, content: str, message_type: str = 'conversational', metadata: Dict[str, Any] = None):
        """Add an assistant message to the conversation history"""
        message = {
            'role': 'assistant',
            'content': content,
            'timestamp': datetime.now(),
            'type': message_type,  # 'conversational' or 'proactive'
            'metadata': metadata or {}
        }
        
        self._add_message(message)
    
    def _add_message(self, message: Dict[str, Any]):
        """Add a message and manage history size"""
        self.conversation_history.append(message)
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_history_size:
            # Keep the most recent messages
            self.conversation_history = self.conversation_history[-self.max_history_size:]
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history"""
        return self.conversation_history.copy()
    
    def get_recent_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent conversation history for context"""
        if limit is None:
            limit = self.limits.get('max_recent_changes', 8)
        
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def get_last_assistant_message(self) -> Optional[Dict[str, Any]]:
        """Get the most recent assistant message"""
        for message in reversed(self.conversation_history):
            if message.get('role') == 'assistant':
                return message
        return None
    
    def get_last_user_message(self) -> Optional[Dict[str, Any]]:
        """Get the most recent user message"""
        for message in reversed(self.conversation_history):
            if message.get('role') == 'user':
                return message
        return None
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get messages of a specific type (e.g., 'proactive', 'conversational')"""
        return [
            msg for msg in self.conversation_history 
            if msg.get('type') == message_type or (message_type == 'user' and msg.get('role') == 'user')
        ]
    
    def get_proactive_comments(self) -> List[Dict[str, Any]]:
        """Get all proactive comments from the conversation"""
        return self.get_messages_by_type('proactive')
    
    def get_conversational_messages(self) -> List[Dict[str, Any]]:
        """Get all conversational (non-proactive) messages"""
        return [
            msg for msg in self.conversation_history
            if msg.get('role') == 'user' or (msg.get('role') == 'assistant' and msg.get('type') == 'conversational')
        ]
    
    def format_history_for_llm(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Format conversation history for LLM API calls"""
        recent_history = self.get_recent_history(limit)
        
        formatted_messages = []
        for message in recent_history:
            # Skip feedback messages to avoid confusing the LLM
            if message.get('is_feedback', False):
                continue
            
            formatted_message = {
                'role': message['role'],
                'content': message['content']
            }
            formatted_messages.append(formatted_message)
        
        return formatted_messages
    
    def build_context_summary(self) -> str:
        """Build a summary of recent conversation for context"""
        recent_messages = self.get_recent_history(6)
        
        if not recent_messages:
            return "No recent conversation history."
        
        summary_parts = ["Recent conversation:"]
        
        for message in recent_messages:
            if message.get('is_feedback', False):
                continue  # Skip feedback messages in summary
            
            role = "You" if message['role'] == 'assistant' else "Developer"
            content = message['content']
            
            # Truncate long messages
            if len(content) > 100:
                content = content[:97] + "..."
            
            summary_parts.append(f"{role}: {content}")
        
        return "\\n".join(summary_parts)
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current session"""
        total_messages = len(self.conversation_history)
        user_messages = sum(1 for msg in self.conversation_history if msg.get('role') == 'user')
        assistant_messages = sum(1 for msg in self.conversation_history if msg.get('role') == 'assistant')
        proactive_comments = sum(1 for msg in self.conversation_history if msg.get('type') == 'proactive')
        feedback_messages = sum(1 for msg in self.conversation_history if msg.get('is_feedback', False))
        
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return {
            'session_duration_seconds': session_duration,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'proactive_comments': proactive_comments,
            'feedback_messages': feedback_messages,
            'conversational_messages': assistant_messages - proactive_comments,
            'average_messages_per_minute': (total_messages / (session_duration / 60)) if session_duration > 0 else 0
        }
    
    def search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversation history for messages containing query"""
        query_lower = query.lower()
        
        matching_messages = []
        for message in reversed(self.conversation_history):
            if query_lower in message.get('content', '').lower():
                matching_messages.append(message)
                if len(matching_messages) >= limit:
                    break
        
        return matching_messages
    
    def get_messages_since(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """Get messages since a specific timestamp"""
        return [
            msg for msg in self.conversation_history
            if msg.get('timestamp', datetime.min) >= timestamp
        ]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.session_start_time = datetime.now()
    
    def export_history(self) -> Dict[str, Any]:
        """Export conversation history for persistence or analysis"""
        return {
            'session_start': self.session_start_time.isoformat(),
            'export_time': datetime.now().isoformat(),
            'statistics': self.get_session_statistics(),
            'messages': [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'type': msg.get('type'),
                    'is_feedback': msg.get('is_feedback', False),
                    'metadata': msg.get('metadata', {})
                }
                for msg in self.conversation_history
            ]
        }
    
    def import_history(self, exported_data: Dict[str, Any]):
        """Import previously exported conversation history"""
        try:
            self.session_start_time = datetime.fromisoformat(exported_data['session_start'])
            
            for msg_data in exported_data['messages']:
                message = {
                    'role': msg_data['role'],
                    'content': msg_data['content'],
                    'timestamp': datetime.fromisoformat(msg_data['timestamp']),
                    'type': msg_data.get('type'),
                    'is_feedback': msg_data.get('is_feedback', False),
                    'metadata': msg_data.get('metadata', {})
                }
                self.conversation_history.append(message)
                
        except Exception as e:
            print(f"Error importing history: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get history manager status"""
        return {
            'name': 'HistoryManager',
            'total_messages': len(self.conversation_history),
            'max_history_size': self.max_history_size,
            'session_start': self.session_start_time.isoformat(),
            'statistics': self.get_session_statistics()
        }