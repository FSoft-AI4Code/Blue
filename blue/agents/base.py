"""
Base Agent Class

Provides common functionality for all Blue agents.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from termcolor import colored


class BaseAgent(ABC):
    """Abstract base class for all Blue agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    def initialize(self):
        """Initialize the agent"""
        pass
    
    def _timestamp(self) -> str:
        """Get current timestamp string"""
        return datetime.now().strftime("%H:%M:%S")
    
    def _log(self, message: str, level: str = "info"):
        """Log a message with timestamp and agent name"""
        color_map = {
            "info": "white",
            "debug": "cyan", 
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }
        
        color = color_map.get(level, "white")
        formatted_message = f"[{self._timestamp()}] {self.agent_name}: {message}"
        print(colored(formatted_message, color))
    
    def _log_debug(self, message: str):
        """Log a debug message"""
        self._log(f"[DEBUG] {message}", "debug")
    
    def _log_warning(self, message: str):
        """Log a warning message"""
        self._log(f"[WARNING] {message}", "warning")
    
    def _log_error(self, message: str):
        """Log an error message"""
        self._log(f"[ERROR] {message}", "error")
    
    def _log_success(self, message: str):
        """Log a success message"""
        self._log(message, "success")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'name': self.agent_name,
            'initialized': hasattr(self, '_initialized'),
            'timestamp': datetime.now().isoformat()
        }