"""
Blue Conversation Package

Manages user interactions, chat history, and feedback processing.
Handles the conversational interface between user and agents.
"""

from .chat_manager import ChatManager
from .feedback_processor import FeedbackProcessor
from .history_manager import HistoryManager

__all__ = ["ChatManager", "FeedbackProcessor", "HistoryManager"]