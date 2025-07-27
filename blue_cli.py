"""
Blue CLI - Main system coordinator

Coordinates the observer and navigator agents for ambient pair programming.
"""

import os
import threading
import time
from datetime import datetime
from termcolor import colored
from typing import Dict, Any

from blue.config import get_config
from blue.agents.observer import ObserverAgent
from blue.agents.navigator import NavigatorAgent


class BlueCLI:
    """Main coordinator for the Blue ambient pair programming system"""
    
    def __init__(self, directory_path: str, llm_provider: str = "anthropic", config_path: str = None):
        self.directory_path = directory_path
        self.llm_provider = llm_provider
        self.running = False
        
        # Load configuration
        self.config = get_config(config_path)
        
        # Initialize agents
        self.observer = ObserverAgent(self.config, directory_path)
        self.navigator = NavigatorAgent(self.config, llm_provider)
        
        # Set up communication between agents
        self.observer.set_navigator(self.navigator)
        self.navigator.set_observer(self.observer)
        
        self._log_success(f"Blue CLI initialized for directory: {directory_path}")
        self._display_startup_info()
    
    def _timestamp(self) -> str:
        """Get current timestamp string"""
        return datetime.now().strftime("%H:%M:%S")
    
    def _log_success(self, message: str):
        """Log success message"""
        print(colored(f"[{self._timestamp()}] {message}", "cyan"))
    
    def _log_info(self, message: str):
        """Log info message"""
        print(colored(f"[{self._timestamp()}] {message}", "green"))
    
    def _log_warning(self, message: str):
        """Log warning message"""
        print(colored(f"[{self._timestamp()}] {message}", "yellow"))
    
    def _log_error(self, message: str):
        """Log error message"""
        print(colored(f"[{self._timestamp()}] {message}", "red"))
    
    def _display_startup_info(self):
        """Display startup information"""
        print()
        print(colored("🤖 Blue - Ambient Pair Programming Assistant", "cyan", attrs=['bold']))
        print(colored("=" * 50, "cyan"))
        
        # Display configuration info
        provider = self.llm_provider.upper()
        print(colored(f"🧠 LLM Provider: {provider}", "green"))
        print(colored(f"📁 Monitoring: {self.directory_path}", "green"))
        
        # Display monitoring settings
        file_monitor = self.observer.file_monitor
        extensions = file_monitor.get_supported_extensions()
        print(colored(f"📄 File Types: {', '.join(extensions[:8])}{'...' if len(extensions) > 8 else ''}", "green"))
        
        # Display decision settings
        if self.config.get('limits', {}).get('enable_llm_decision', False):
            print(colored("🎯 Dynamic Decision Making: Enabled", "green"))
        if self.config.get('limits', {}).get('enable_adaptive_learning', False):
            print(colored("🧠 Adaptive Learning: Enabled", "green"))
        
        print(colored("=" * 50, "cyan"))
        print()
    
    def start(self):
        """Start the Blue CLI system"""
        self.running = True
        
        self._log_info("Starting file monitoring...")
        
        # Start the observer in a separate thread
        observer_thread = threading.Thread(target=self.observer.start_monitoring)
        observer_thread.daemon = True
        observer_thread.start()
        
        # Give the observer a moment to start
        time.sleep(0.5)
        
        # Start interactive mode
        self._interactive_mode()
    
    def _interactive_mode(self):
        """Handle interactive user input"""
        self._log_info("Blue CLI is now active. Type your thoughts or questions:")
        print(colored("Type 'quit', 'exit', or 'status' for system status.", "yellow"))
        print()
        
        try:
            while self.running:
                try:
                    user_input = input(colored("> ", "blue", attrs=['bold']))
                    
                    if user_input.lower() in ['quit', 'exit']:
                        self._shutdown()
                        break
                    elif user_input.lower() == 'status':
                        self._display_status()
                        continue
                    elif user_input.lower() == 'help':
                        self._display_help()
                        continue
                    
                    if user_input.strip():
                        # Send user input to navigator for processing
                        self.navigator.handle_user_input(user_input)
                        
                except KeyboardInterrupt:
                    print(colored(f"\\n[{self._timestamp()}] Shutting down...", "red"))
                    self._shutdown()
                    break
                except EOFError:
                    self._shutdown()
                    break
                    
        except Exception as e:
            self._log_error(f"Error in interactive mode: {e}")
            try:
                self._shutdown()
            except Exception:
                pass  # Ignore shutdown errors
    
    def _display_status(self):
        """Display system status"""
        print()
        print(colored("📊 SYSTEM STATUS", "cyan", attrs=['bold']))
        print(colored("-" * 30, "cyan"))
        
        # Observer status
        observer_status = self.observer.get_status()
        print(colored(f"👁️  Observer: {'Running' if observer_status['monitoring'] else 'Stopped'}", "green" if observer_status['monitoring'] else "red"))
        print(colored(f"   Buffer: {observer_status['buffer_size']}/10 events", "white"))
        print(colored(f"   Score: {observer_status['buffer_score']}/{observer_status['score_threshold']}", "white"))
        
        # Navigator status
        navigator_status = self.navigator.get_status()
        print(colored(f"🧠 Navigator: {'Available' if navigator_status['llm_available'] else 'Unavailable'}", "green" if navigator_status['llm_available'] else "red"))
        print(colored(f"   Provider: {navigator_status['provider'].upper()}", "white"))
        print(colored(f"   Conversations: {navigator_status['conversation_entries']}", "white"))
        
        # Feedback stats
        if navigator_status.get('feedback_stats'):
            stats = navigator_status['feedback_stats']
            if stats['total_feedback'] > 0:
                print(colored(f"   Feedback: +{stats['positive_feedback']} -{stats['negative_feedback']}", "white"))
                print(colored(f"   Threshold: {stats['current_threshold']} (initial: {stats['initial_threshold']})", "white"))
        
        print()
    
    def _display_help(self):
        """Display help information"""
        print()
        print(colored("🔧 BLUE COMMANDS", "cyan", attrs=['bold']))
        print(colored("-" * 30, "cyan"))
        print(colored("status", "green") + " - Show system status")
        print(colored("help", "green") + " - Show this help")
        print(colored("quit/exit", "green") + " - Stop Blue and exit")
        print()
        print(colored("💡 FEEDBACK", "cyan", attrs=['bold']))
        print(colored("-" * 30, "cyan"))
        print("After Blue comments, you can provide feedback:")
        print(colored("'good', 'helpful', 'thanks'", "green") + " - Positive feedback (more comments)")
        print(colored("'bad', 'annoying', 'stop'", "red") + " - Negative feedback (fewer comments)")
        print()
    
    def _shutdown(self):
        """Clean shutdown of the system"""
        self.running = False
        
        # Stop observer
        if hasattr(self.observer, 'stop_monitoring'):
            self.observer.stop_monitoring()
        
        # Display final stats
        if hasattr(self.navigator, 'feedback_system') and self.navigator.feedback_system:
            stats = self.navigator.feedback_system.get_feedback_stats()
            if stats['total_feedback'] > 0:
                print()
                print(colored("📈 SESSION SUMMARY", "cyan", attrs=['bold']))
                print(colored("-" * 30, "cyan"))
                print(colored(f"Total feedback received: {stats['total_feedback']}", "white"))
                print(colored(f"Positive feedback: {stats['positive_feedback']}", "green"))
                print(colored(f"Negative feedback: {stats['negative_feedback']}", "red"))
                print(colored(f"Final threshold: {stats['current_threshold']} (started at {stats['initial_threshold']})", "white"))
        
        self._log_success("Blue CLI stopped. Thanks for coding with Blue! 🤖")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'running': self.running,
            'directory_path': self.directory_path,
            'llm_provider': self.llm_provider,
            'observer_status': self.observer.get_status(),
            'navigator_status': self.navigator.get_status()
        }