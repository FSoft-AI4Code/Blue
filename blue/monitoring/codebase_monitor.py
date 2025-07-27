"""
Codebase Monitor

Pure mechanical file system monitoring. Watches for changes, manages buffers,
and triggers processing when thresholds are met. No intelligence or LLM interaction.
"""

import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .change_analyzer import ChangeAnalyzer, ChangeEvent


class BlueFileSystemEventHandler(FileSystemEventHandler):
    """Custom file system event handler for Blue"""
    
    def __init__(self, codebase_monitor):
        super().__init__()
        self.codebase_monitor = codebase_monitor
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        if self.codebase_monitor.should_monitor_file(event.src_path):
            self.codebase_monitor._handle_file_change('modified', event.src_path)
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        if self.codebase_monitor.should_monitor_file(event.src_path):
            self.codebase_monitor._handle_file_change('created', event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return
        
        # Note: We can't check if deleted file should be monitored since it's gone
        # So we'll let the callback decide
        self.codebase_monitor._handle_file_change('deleted', event.src_path)
    
    def on_moved(self, event):
        """Handle file move events"""
        if event.is_directory:
            return
        
        # Check both source and destination paths
        src_monitored = self.codebase_monitor.should_monitor_file(event.src_path)
        dest_monitored = self.codebase_monitor.should_monitor_file(event.dest_path)
        
        if src_monitored or dest_monitored:
            self.codebase_monitor._handle_file_change('moved', event.src_path, event.dest_path)


class CodebaseMonitor:
    """Monitors codebase for changes and manages event processing"""
    
    def __init__(self, config: Dict[str, Any], directory_path: str):
        self.config = config
        self.directory_path = directory_path
        self.running = False
        
        # Core components
        self.change_analyzer = ChangeAnalyzer(config)
        
        # File monitoring configuration
        self.monitoring_config = config.get('monitoring', {})
        
        # Change buffer and state
        self.change_buffer = deque(maxlen=10)
        self.buffer_score = 0
        self.last_activity_time = time.time()
        self.last_processing_time = 0
        
        # Configuration
        self.limits = config.get('limits', {})
        self.buffer_threshold = self.limits.get('buffer_threshold', 4)
        self.min_buffer_size = self.limits.get('min_buffer_size', 3)
        self.processing_cooldown = self.limits.get('processing_cooldown', 30)
        self.score_threshold = self.limits.get('score_threshold', 5)
        self.idle_threshold = self.limits.get('idle_threshold', 30)
        self.max_buffer_age = self.limits.get('max_buffer_age', 120)
        
        # External triggers
        self.change_handlers: List[callable] = []
        
        # Observer for file system events
        self.observer = None
        
        print(f"[{self._timestamp()}] CodebaseMonitor initialized for: {directory_path}")
    
    def should_monitor_file(self, file_path: str) -> bool:
        """Check if a file should be monitored based on configuration"""
        path = Path(file_path)
        
        # Check file extension
        supported_extensions = self.monitoring_config.get('supported_extensions', [])
        if supported_extensions and path.suffix not in supported_extensions:
            return False
        
        # Check if file is in ignored directories
        ignore_directories = self.monitoring_config.get('ignore_directories', [])
        for ignore_dir in ignore_directories:
            if ignore_dir in path.parts:
                return False
        
        # Check ignored file patterns
        ignore_files = self.monitoring_config.get('ignore_files', [])
        for ignore_pattern in ignore_files:
            if path.name == ignore_pattern or (ignore_pattern.startswith('*.') and path.suffix == ignore_pattern[1:]):
                return False
        
        return True
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return self.monitoring_config.get('supported_extensions', [])
    
    def get_ignore_patterns(self) -> Dict[str, List[str]]:
        """Get ignore patterns for files and directories"""
        return {
            'directories': self.monitoring_config.get('ignore_directories', []),
            'files': self.monitoring_config.get('ignore_files', [])
        }
    
    def filter_monitored_files(self, file_paths: List[str]) -> List[str]:
        """Filter a list of file paths to only include monitored files"""
        return [path for path in file_paths if self.should_monitor_file(path)]
    
    def scan_directory(self, directory: str) -> List[str]:
        """Scan a directory for monitorable files"""
        monitored_files = []
        
        for root, dirs, files in os.walk(directory):
            # Filter out ignored directories
            ignore_directories = self.monitoring_config.get('ignore_directories', [])
            dirs[:] = [d for d in dirs if d not in ignore_directories]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_monitor_file(file_path):
                    monitored_files.append(file_path)
        
        return monitored_files

    def _timestamp(self) -> str:
        """Get current timestamp string"""
        return datetime.now().strftime("%H:%M:%S")
    
    def add_change_handler(self, handler: callable):
        """Add a handler to be called when changes are processed"""
        self.change_handlers.append(handler)
    
    def start_monitoring(self):
        """Start monitoring the directory for changes"""
        self.running = True
        self.observer = Observer()
        
        # Use the file system event handler
        event_handler = BlueFileSystemEventHandler(self)
        
        self.observer.schedule(event_handler, self.directory_path, recursive=True)
        self.observer.start()
        
        print(f"[{self._timestamp()}] File monitoring started for: {self.directory_path}")
        
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
        print(f"[{self._timestamp()}] File monitoring stopped")
    
    def _handle_file_change(self, event_type: str, file_path: str, dest_path: str = None):
        """Handle a file system change event"""
        # Use change analyzer to process the change
        change_event = self.change_analyzer.analyze_change(file_path, event_type)
        
        if not change_event:
            return
        
        # Add to buffer
        self.change_buffer.append(change_event)
        self.buffer_score += change_event.score
        self.last_activity_time = time.time()
        
        # Display the change
        self._display_change(change_event)
        
        # Check if we should trigger processing
        if self._should_trigger_processing():
            self._trigger_change_processing()
    
    def _should_trigger_processing(self) -> bool:
        """Determine if we should trigger change processing"""
        current_time = time.time()
        buffer_size = len(self.change_buffer)
        
        # Clean old buffer entries first
        self._clean_old_buffer_entries(current_time)
        
        # Don't process if we don't have minimum events
        if buffer_size < self.min_buffer_size:
            return False
            
        # Respect cooldown period
        if current_time - self.last_processing_time < self.processing_cooldown:
            return False
        
        # Score-based trigger conditions (in order of priority):
        
        # 1. Score threshold reached (primary trigger)
        if self.buffer_score >= self.score_threshold:
            print(f"[DEBUG] Score threshold reached: {self.buffer_score} >= {self.score_threshold}")
            return True
            
        # 2. Idle threshold exceeded (secondary trigger)
        idle_time = current_time - self.last_activity_time
        if idle_time >= self.idle_threshold and buffer_size > 0:
            print(f"[DEBUG] Idle threshold reached: {idle_time:.1f}s >= {self.idle_threshold}s")
            return True
            
        # 3. Pattern-based conditions
        if self._has_function_completion() or self._has_architectural_change():
            return True
            
        # 4. Buffer size fallback
        if buffer_size >= self.buffer_threshold:
            return True
            
        return False
    
    def _trigger_change_processing(self):
        """Trigger processing of accumulated changes"""
        changes_summary = self._get_changes_summary()
        
        # Add processing context
        changes_summary['processing_reason'] = self._get_processing_reason()
        changes_summary['priority_level'] = self._assess_priority_level()
        changes_summary['buffer_score'] = self.buffer_score
        changes_summary['score_breakdown'] = self._get_score_breakdown()
        
        # Notify all change handlers
        for handler in self.change_handlers:
            try:
                handler(changes_summary)
            except Exception as e:
                print(f"[ERROR] Error in change handler: {e}")
        
        # Update processing time and clear buffer
        self.last_processing_time = time.time()
        self._clear_buffer()
    
    def _clean_old_buffer_entries(self, current_time: float):
        """Remove entries older than max_buffer_age"""
        cutoff_time = current_time - self.max_buffer_age
        initial_size = len(self.change_buffer)
        
        # Remove old entries and recalculate score
        old_buffer = list(self.change_buffer)
        self.change_buffer.clear()
        self.buffer_score = 0
        
        for event in old_buffer:
            if event.timestamp.timestamp() >= cutoff_time:
                self.change_buffer.append(event)
                self.buffer_score += event.score
        
        if len(self.change_buffer) < initial_size:
            print(f"[DEBUG] Cleaned {initial_size - len(self.change_buffer)} old entries, score now {self.buffer_score}")
    
    def _has_function_completion(self) -> bool:
        """Check if recent changes suggest function completion"""
        recent_events = list(self.change_buffer)[-3:]
        for event in recent_events:
            if 'functions_added' in event.details and event.details['functions_added']:
                return True
        return False
    
    def _has_architectural_change(self) -> bool:
        """Check for architectural changes (new files, imports, etc.)"""
        recent_events = list(self.change_buffer)[-4:]
        
        # Look for file creation followed by modifications
        has_creation = any(event.event_type == 'created' for event in recent_events)
        has_modification = any(event.event_type == 'modified' for event in recent_events)
        
        return has_creation and has_modification
    
    def _get_processing_reason(self) -> str:
        """Determine why we're processing now"""
        current_time = time.time()
        idle_time = current_time - self.last_activity_time
        
        if self.buffer_score >= self.score_threshold:
            return 'score_threshold'
        elif idle_time >= self.idle_threshold:
            return 'idle_timeout'
        elif self._has_function_completion():
            return 'function_completion'
        elif self._has_architectural_change():
            return 'architectural_change'
        elif len(self.change_buffer) >= self.buffer_threshold:
            return 'buffer_full'
        else:
            return 'threshold_met'
    
    def _assess_priority_level(self) -> str:
        """Assess priority level based on buffer score and content"""
        # High priority: high score or critical patterns
        if self.buffer_score >= self.score_threshold * 1.5:
            return 'high'
        
        # Medium priority: moderate score or function completion
        if self.buffer_score >= self.score_threshold or self._has_function_completion():
            return 'medium'
            
        # Low priority: low score changes
        return 'low'
    
    def _get_changes_summary(self) -> Dict[str, Any]:
        """Get summary of recent changes"""
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
    
    def _get_score_breakdown(self) -> Dict[str, Any]:
        """Get detailed breakdown of current buffer score"""
        breakdown = {
            'total_score': self.buffer_score,
            'event_scores': [],
            'score_threshold': self.score_threshold
        }
        
        for event in self.change_buffer:
            event_info = {
                'file': os.path.basename(event.file_path),
                'type': event.event_type,
                'score': event.score,
                'timestamp': event.timestamp.strftime('%H:%M:%S')
            }
            breakdown['event_scores'].append(event_info)
            
        return breakdown
    
    def _clear_buffer(self):
        """Clear the buffer and reset scoring state"""
        self.change_buffer.clear()
        self.buffer_score = 0
        print(f"[DEBUG] Buffer cleared, score reset to 0")
    
    def _display_change(self, change_event: ChangeEvent):
        """Display file change to terminal"""
        file_name = os.path.basename(change_event.file_path)
        
        # Format details
        details_str = ""
        if 'lines_changed' in change_event.details:
            details_str = f": {change_event.details['lines_changed']}"
        
        if 'functions_added' in change_event.details and change_event.details['functions_added']:
            func_names = ', '.join(change_event.details['functions_added'])
            details_str += f", new functions: {func_names}"
        
        # Color code by event type
        if change_event.event_type == 'created':
            icon = '+'
            color = 'green'
        elif change_event.event_type == 'modified':
            icon = '~'
            color = 'blue'
        else:  # deleted
            icon = '-'
            color = 'red'
        
        from termcolor import colored
        message = f"[{change_event.timestamp.strftime('%H:%M:%S')}] {icon} File {file_name} {change_event.event_type}{details_str}"
        print(colored(message, color))
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status"""
        return {
            'name': 'CodebaseMonitor',
            'directory_path': self.directory_path,
            'monitoring': self.running,
            'buffer_size': len(self.change_buffer),
            'buffer_score': self.buffer_score,
            'last_activity': datetime.fromtimestamp(self.last_activity_time).isoformat() if self.last_activity_time else None,
            'score_threshold': self.score_threshold,
            'idle_threshold': self.idle_threshold
        }