"""
Blue CLI - Main system coordinator
"""

import os
import threading
import time
from datetime import datetime
from termcolor import colored
from typing import Dict, Any

from observer_agent import ObserverAgent
from navigator_agent import NavigatorAgent


class BlueCLI:
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.running = False
        
        # Initialize agents
        self.observer = ObserverAgent(directory_path)
        self.navigator = NavigatorAgent()
        
        # Set up communication between agents
        self.observer.set_navigator(self.navigator)
        self.navigator.set_observer(self.observer)
        
        print(colored(f"[{self._timestamp()}] Blue CLI initialized for directory: {directory_path}", "cyan"))
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
    
    def start(self):
        """Start the Blue CLI system"""
        self.running = True
        
        print(colored(f"[{self._timestamp()}] Starting file monitoring...", "green"))
        
        # Start the observer in a separate thread
        observer_thread = threading.Thread(target=self.observer.start_monitoring)
        observer_thread.daemon = True
        observer_thread.start()
        
        # Start interactive mode
        self._interactive_mode()
    
    def _interactive_mode(self):
        """Handle interactive user input"""
        print(colored(f"[{self._timestamp()}] Blue CLI is now active. Type your thoughts or questions:", "green"))
        print(colored("Type 'quit' or 'exit' to stop monitoring.", "yellow"))
        print()
        
        try:
            while self.running:
                try:
                    user_input = input(colored("> ", "blue"))
                    
                    if user_input.lower() in ['quit', 'exit']:
                        self._shutdown()
                        break
                    
                    if user_input.strip():
                        # Send user input to navigator for processing
                        self.navigator.handle_user_input(user_input)
                        
                except KeyboardInterrupt:
                    print(colored(f"\n[{self._timestamp()}] Shutting down...", "red"))
                    self._shutdown()
                    break
                except EOFError:
                    self._shutdown()
                    break
                    
        except Exception as e:
            print(colored(f"[{self._timestamp()}] Error in interactive mode: {e}", "red"))
            try:
                self._shutdown()
            except Exception:
                pass  # Ignore shutdown errors
    
    def _shutdown(self):
        """Clean shutdown of the system"""
        self.running = False
        if hasattr(self.observer, 'stop_monitoring'):
            self.observer.stop_monitoring()
        print(colored(f"[{self._timestamp()}] Blue CLI stopped.", "cyan"))