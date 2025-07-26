"""
Observer Agent - Monitors file changes and buffers events
"""

import os
import re
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from termcolor import colored


class ChangeEvent:
    def __init__(self, file_path: str, event_type: str, timestamp: datetime, details: Dict[str, Any] = None):
        self.file_path = file_path
        self.event_type = event_type  # 'modified', 'created', 'deleted'
        self.timestamp = timestamp
        self.details = details or {}
        
    def __str__(self):
        return f"{self.event_type.capitalize()} {self.file_path} at {self.timestamp.strftime('%H:%M:%S')}"


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, observer_agent):
        self.observer_agent = observer_agent
        
    def on_modified(self, event):
        if not event.is_directory:
            self.observer_agent._handle_file_change(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory:
            self.observer_agent._handle_file_change(event.src_path, 'created')
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.observer_agent._handle_file_change(event.src_path, 'deleted')


class ObserverAgent:
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.navigator = None
        self.observer = None
        self.running = False
        
        # Change buffer (keeps last 10 events)
        self.change_buffer = deque(maxlen=10)
        self.buffer_threshold = 5
        
        # Track recent file contents to detect meaningful changes
        self.file_contents_cache = {}
        
        # Supported file extensions
        self.supported_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', 
                                   '.rs', '.php', '.rb', '.swift', '.kt', '.cs', '.vue', '.html', '.css', '.scss'}
        
        print(colored(f"[{self._timestamp()}] Observer Agent initialized", "yellow"))
    
    def set_navigator(self, navigator):
        """Set reference to navigator agent"""
        self.navigator = navigator
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
    
    def _is_relevant_file(self, file_path: str) -> bool:
        """Check if file is relevant for monitoring"""
        path = Path(file_path)
        
        # Skip hidden files and directories
        if any(part.startswith('.') for part in path.parts):
            return False
            
        # Skip common build/cache directories
        skip_dirs = {'node_modules', '__pycache__', '.git', 'build', 'dist', 'target', '.pytest_cache'}
        if any(skip_dir in path.parts for skip_dir in skip_dirs):
            return False
            
        # Check file extension
        return path.suffix.lower() in self.supported_extensions
    
    def _handle_file_change(self, file_path: str, event_type: str):
        """Handle a file system change event"""
        if not self._is_relevant_file(file_path):
            return
            
        timestamp = datetime.now()
        
        # Analyze the change for meaningful content
        details = self._analyze_file_change(file_path, event_type)
        
        change_event = ChangeEvent(file_path, event_type, timestamp, details)
        self.change_buffer.append(change_event)
        
        # Display the change
        self._display_change(change_event)
        
        # Check if we should trigger agent processing
        if self._should_trigger_processing():
            self._trigger_navigator_processing()
    
    def _analyze_file_change(self, file_path: str, event_type: str) -> Dict[str, Any]:
        """Analyze the file change for meaningful content"""
        details = {}
        
        if event_type == 'deleted':
            details['lines_changed'] = 'File deleted'
            return details
            
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    current_content = f.read()
                
                # Get previous content if available
                previous_content = self.file_contents_cache.get(file_path, '')
                
                # Basic line count analysis
                current_lines = current_content.split('\n')
                previous_lines = previous_content.split('\n')
                
                line_diff = len(current_lines) - len(previous_lines)
                details['lines_changed'] = f"{'+' if line_diff > 0 else ''}{line_diff} lines"
                
                # Detect function additions/modifications (basic pattern matching)
                functions_added = self._detect_functions(current_content, previous_content)
                if functions_added:
                    details['functions_added'] = functions_added
                
                # Update cache
                self.file_contents_cache[file_path] = current_content
                
        except Exception as e:
            details['error'] = f"Could not analyze: {str(e)}"
            
        return details
    
    def _detect_functions(self, current_content: str, previous_content: str) -> List[str]:
        """Detect newly added functions (basic implementation)"""
        functions = []
        
        # Python function pattern
        py_pattern = r'^def\s+(\w+)\s*\('
        # JavaScript function patterns
        js_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*\(',
            r'(\w+)\s*:\s*function\s*\(',
            r'(\w+)\s*=>\s*'
        ]
        
        patterns = [py_pattern] + js_patterns
        
        for pattern in patterns:
            current_functions = set(re.findall(pattern, current_content, re.MULTILINE))
            previous_functions = set(re.findall(pattern, previous_content, re.MULTILINE))
            new_functions = current_functions - previous_functions
            functions.extend(new_functions)
        
        return functions
    
    def _display_change(self, change_event: ChangeEvent):
        """Display file change to terminal with color coding"""
        file_name = os.path.basename(change_event.file_path)
        
        # Color code by event type
        if change_event.event_type == 'created':
            color = 'green'
            icon = '+'
        elif change_event.event_type == 'modified':
            color = 'blue'
            icon = '~'
        else:  # deleted
            color = 'red'
            icon = '-'
        
        # Format details
        details_str = ""
        if 'lines_changed' in change_event.details:
            details_str = f": {change_event.details['lines_changed']}"
        
        if 'functions_added' in change_event.details and change_event.details['functions_added']:
            func_names = ', '.join(change_event.details['functions_added'])
            details_str += f", new functions: {func_names}"
        
        message = f"[{change_event.timestamp.strftime('%H:%M:%S')}] {icon} File {file_name} {change_event.event_type}{details_str}"
        print(colored(message, color))
    
    def _should_trigger_processing(self) -> bool:
        """Determine if we should trigger navigator processing"""
        # Trigger if buffer reaches threshold
        if len(self.change_buffer) >= self.buffer_threshold:
            return True
            
        # Trigger if we detect function completion
        recent_events = list(self.change_buffer)[-3:]  # Last 3 events
        for event in recent_events:
            if 'functions_added' in event.details and event.details['functions_added']:
                return True
                
        return False
    
    def _trigger_navigator_processing(self):
        """Send accumulated changes to navigator for processing"""
        if self.navigator:
            changes_summary = self._get_changes_summary()
            self.navigator.process_changes(changes_summary)
            # Clear some buffer space but keep recent changes
            while len(self.change_buffer) > 3:
                self.change_buffer.popleft()
    
    def _get_changes_summary(self) -> Dict[str, Any]:
        """Get summary of recent changes for navigator"""
        summary = {
            'total_changes': len(self.change_buffer),
            'files_affected': len(set(event.file_path for event in self.change_buffer)),
            'changes': []
        }
        
        for event in self.change_buffer:
            change_info = {
                'file': os.path.basename(event.file_path),
                'type': event.event_type,
                'details': event.details,
                'timestamp': event.timestamp.isoformat()
            }
            summary['changes'].append(change_info)
            
        return summary
    
    def start_monitoring(self):
        """Start monitoring the directory for changes"""
        self.running = True
        self.observer = Observer()
        
        event_handler = FileChangeHandler(self)
        self.observer.schedule(event_handler, self.directory_path, recursive=True)
        
        self.observer.start()
        print(colored(f"[{self._timestamp()}] File monitoring started for: {self.directory_path}", "green"))
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        print(colored(f"[{self._timestamp()}] File monitoring stopped", "yellow"))