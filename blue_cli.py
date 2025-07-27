"""
Blue CLI - Main system coordinator (Refactored)

Coordinates the codebase monitor and navigator agent for ambient pair programming.
Uses the new clean architecture with proper separation of concerns.
"""

import os
import threading
import time
from datetime import datetime
from termcolor import colored
from typing import Dict, Any

from blue.config import get_config
from blue.monitoring.codebase_monitor import CodebaseMonitor
from blue.agents.navigator_agent import NavigatorAgent


class BlueCLI:
    """Main coordinator for the Blue ambient pair programming system"""
    
    def __init__(self, directory_path: str, llm_provider: str = "anthropic", config_path: str = None):
        self.directory_path = directory_path
        self.llm_provider = llm_provider
        self.running = False
        
        # Load configuration
        self.config = get_config(config_path)
        
        # Initialize components with new architecture
        self.codebase_monitor = CodebaseMonitor(self.config, directory_path)
        self.navigator_agent = NavigatorAgent(self.config, llm_provider)
        
        # Set up communication between components
        self.codebase_monitor.add_change_handler(self.navigator_agent.process_code_changes)
        self.navigator_agent.set_codebase_monitor(self.codebase_monitor)
        
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
        
        # Display agent-specific configuration info
        navigator_status = self.navigator_agent.get_status()
        print(colored(f"🧠 NavigatorAgent: {navigator_status['provider'].upper()} ({navigator_status['model']})", "green"))
        
        # Display intervention agent info if available
        if navigator_status.get('intervention_agent_status'):
            intervention_status = navigator_status['intervention_agent_status']
            intervention_info = intervention_status.get('llm_info', {})
            intervention_provider = intervention_info.get('provider', 'unknown').upper()
            intervention_model = intervention_info.get('model', 'unknown')
            print(colored(f"⚡ InterventionAgent: {intervention_provider} ({intervention_model})", "green"))
        
        print(colored(f"📁 Monitoring: {self.directory_path}", "green"))
        
        # Display monitoring settings
        extensions = self.codebase_monitor.get_supported_extensions()
        print(colored(f"📄 File Types: {', '.join(extensions[:8])}{'...' if len(extensions) > 8 else ''}", "green"))
        
        # Display intelligence features
        if self.config.get('limits', {}).get('enable_llm_decision', False):
            print(colored("🎯 Smart Intervention: Enabled", "green"))
        if self.config.get('limits', {}).get('enable_adaptive_learning', False):
            print(colored("🧠 Adaptive Learning: Enabled", "green"))
        
        print(colored("=" * 50, "cyan"))
        print()
    
    def start(self):
        """Start the Blue CLI system"""
        self.running = True
        
        self._log_info("Starting codebase monitoring...")
        
        # Start the codebase monitor in a separate thread
        monitor_thread = threading.Thread(target=self.codebase_monitor.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Give the monitor a moment to start
        time.sleep(0.5)
        
        # Start interactive mode
        self._interactive_mode()
    
    def _interactive_mode(self):
        """Handle interactive user input"""
        self._log_info("Blue CLI is now active. Type your thoughts or questions:")
        print(colored("Type 'quit', 'exit', 'status', or 'help' for commands.", "yellow"))
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
                    elif user_input.lower() == 'clear':
                        self._clear_conversation()
                        continue
                    
                    if user_input.strip():
                        # Send user input to navigator for processing
                        self.navigator_agent.handle_user_input(user_input)
                        
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
        print(colored("-" * 40, "cyan"))
        
        # Codebase Monitor status
        monitor_status = self.codebase_monitor.get_status()
        print(colored(f"👁️  Codebase Monitor: {'Running' if monitor_status['monitoring'] else 'Stopped'}", "green" if monitor_status['monitoring'] else "red"))
        print(colored(f"   Buffer: {monitor_status['buffer_size']}/10 events", "white"))
        print(colored(f"   Score: {monitor_status['buffer_score']}/{monitor_status['score_threshold']}", "white"))
        
        # Navigator Agent status
        navigator_status = self.navigator_agent.get_status()
        print(colored(f"🧠 Navigator Agent: {'Available' if navigator_status['llm_available'] else 'Unavailable'}", "green" if navigator_status['llm_available'] else "red"))
        print(colored(f"   Provider: {navigator_status['provider'].upper()}", "white"))
        print(colored(f"   Model: {navigator_status['model']}", "white"))
        
        # Intervention Agent status
        if navigator_status.get('intervention_agent_status'):
            intervention_status = navigator_status['intervention_agent_status']
            intervention_info = intervention_status.get('llm_info', {})
            print(colored(f"⚡ Intervention Agent: {'Active' if intervention_status['llm_available'] else 'Limited'}", "green" if intervention_status['llm_available'] else "yellow"))
            print(colored(f"   Provider: {intervention_info.get('provider', 'unknown').upper()}", "white"))
            print(colored(f"   Model: {intervention_info.get('model', 'unknown')}", "white"))
        
        # Chat Manager status
        if navigator_status.get('chat_manager_status'):
            chat_status = navigator_status['chat_manager_status']
            print(colored(f"💬 Chat Manager: {'Active' if chat_status['session_active'] else 'Inactive'}", "green" if chat_status['session_active'] else "red"))
            
            if chat_status.get('session_stats'):
                stats = chat_status['session_stats']
                print(colored(f"   Messages: {stats['total_messages']} total, {stats['proactive_comments']} proactive", "white"))
        
        # Feedback stats
        if navigator_status.get('feedback_stats'):
            stats = navigator_status['feedback_stats']
            if stats['total_feedback'] > 0:
                print(colored(f"📊 Learning: {stats['positive_feedback']}👍 {stats['negative_feedback']}👎 (threshold: {stats['current_threshold']})", "white"))
        
        print()
    
    def _display_help(self):
        """Display help information"""
        print()
        print(colored("🔧 BLUE COMMANDS", "cyan", attrs=['bold']))
        print(colored("-" * 30, "cyan"))
        print(colored("status", "green") + " - Show detailed system status")
        print(colored("help", "green") + " - Show this help message")
        print(colored("clear", "green") + " - Clear conversation history")
        print(colored("quit/exit", "green") + " - Stop Blue and exit")
        print()
        print(colored("💡 FEEDBACK SYSTEM", "cyan", attrs=['bold']))
        print(colored("-" * 30, "cyan"))
        print("After Blue provides insights, give feedback to improve:")
        print(colored("'good', 'helpful', 'thanks'", "green") + " - More insights like this")
        print(colored("'bad', 'annoying', 'stop'", "red") + " - Fewer insights like this")
        print()
        print(colored("🏗️ ARCHITECTURE", "cyan", attrs=['bold']))
        print(colored("-" * 30, "cyan"))
        print("🔍 CodebaseMonitor - Watches files and detects changes")
        print("🤖 NavigatorAgent - Main LLM that provides insights")  
        print("⚡ InterventionAgent - Decides when to speak up")
        print("💬 ChatManager - Handles conversations and feedback")
        print()
    
    def _clear_conversation(self):
        """Clear conversation history"""
        if self.navigator_agent.get_chat_manager():
            self.navigator_agent.get_chat_manager().clear_conversation()
        else:
            print(colored("No conversation history to clear.", "yellow"))
    
    def _shutdown(self):
        """Clean shutdown of the system"""
        self.running = False
        
        # Stop codebase monitor
        if hasattr(self.codebase_monitor, 'stop_monitoring'):
            self.codebase_monitor.stop_monitoring()
        
        # End chat session and display summary
        if self.navigator_agent.get_chat_manager():
            self.navigator_agent.get_chat_manager().end_session()
        
        self._log_success("Blue CLI stopped. Thanks for coding with Blue! 🤖")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'running': self.running,
            'directory_path': self.directory_path,
            'llm_provider': self.llm_provider,
            'codebase_monitor_status': self.codebase_monitor.get_status(),
            'navigator_agent_status': self.navigator_agent.get_status()
        }