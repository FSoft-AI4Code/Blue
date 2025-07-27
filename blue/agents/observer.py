"""
Observer Agent

Monitors file changes, buffers events, and triggers navigator processing.
"""

import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from blue.agents.base import BaseAgent
from blue.core.scoring import ScoringSystem
from blue.utils.file_monitor import FileMonitor, BlueFileSystemEventHandler
from blue.utils.patterns import PatternMatcher


class ChangeEvent:
    """Represents a file system change event with metadata"""
    
    def __init__(self, file_path: str, event_type: str, timestamp: datetime, details: Dict[str, Any] = None):
        self.file_path = file_path
        self.event_type = event_type  # 'modified', 'created', 'deleted'
        self.timestamp = timestamp
        self.details = details or {}
        self.score = 0  # Will be calculated
        
    def __str__(self):
        return f"{self.event_type.capitalize()} {self.file_path} at {self.timestamp.strftime('%H:%M:%S')}"


class ObserverAgent(BaseAgent):
    """Observer Agent - Monitors file changes and manages event buffer"""
    
    def __init__(self, config: Dict[str, Any], directory_path: str):
        super().__init__(config)
        self.directory_path = directory_path
        self.navigator = None
        self.observer = None
        self.running = False
        
        # Core components
        self.file_monitor: Optional[FileMonitor] = None
        self.scoring_system: Optional[ScoringSystem] = None
        self.pattern_matcher: Optional[PatternMatcher] = None
        
        # Change buffer and state
        self.change_buffer = deque(maxlen=10)
        self.buffer_score = 0
        self.last_activity_time = time.time()
        self.last_processing_time = 0
        self.file_contents_cache = {}
        
        # Configuration
        self.limits = config.get('limits', {})
        self.buffer_threshold = self.limits.get('buffer_threshold', 4)
        self.min_buffer_size = self.limits.get('min_buffer_size', 3)
        self.processing_cooldown = self.limits.get('processing_cooldown', 30)
        self.score_threshold = self.limits.get('score_threshold', 5)
        self.idle_threshold = self.limits.get('idle_threshold', 30)
        self.max_buffer_age = self.limits.get('max_buffer_age', 120)
        
        self.initialize()
    
    def initialize(self):
        """Initialize the observer agent"""
        try:
            # Initialize core components
            self.file_monitor = FileMonitor(self.config)
            self.scoring_system = ScoringSystem(self.config)
            self.pattern_matcher = PatternMatcher(self.config)
            
            self._log_success(f"Observer Agent initialized for: {self.directory_path}")
            self._initialized = True
            
        except Exception as e:
            self._log_error(f"Failed to initialize: {e}")
    
    def set_navigator(self, navigator):
        """Set reference to navigator agent"""
        self.navigator = navigator
    
    def start_monitoring(self):
        """Start monitoring the directory for changes"""
        self.running = True
        self.observer = Observer()
        
        # Use the new file system event handler
        event_handler = BlueFileSystemEventHandler(
            self.file_monitor, 
            self._handle_file_change
        )
        
        self.observer.schedule(event_handler, self.directory_path, recursive=True)
        self.observer.start()
        
        self._log_success(f"File monitoring started for: {self.directory_path}")
        
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
        self._log_warning("File monitoring stopped")
    
    def _handle_file_change(self, event_type: str, file_path: str, dest_path: str = None):
        """Handle a file system change event"""
        if not self.file_monitor.should_monitor_file(file_path):
            return
            
        timestamp = datetime.now()
        
        # Analyze the change for meaningful content
        details = self._analyze_file_change(file_path, event_type)
        
        # Create change event
        change_event = ChangeEvent(file_path, event_type, timestamp, details)
        
        # Calculate score for this change
        change_score = self._calculate_change_score(file_path, details)
        change_event.score = change_score
        
        # Add to buffer
        self.change_buffer.append(change_event)
        self.buffer_score += change_score
        self.last_activity_time = time.time()
        
        # Display the change
        self._display_change(change_event)
        
        # Check if we should trigger processing
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
                current_lines = current_content.split('\\n')
                previous_lines = previous_content.split('\\n')
                
                line_diff = len(current_lines) - len(previous_lines)
                details['lines_changed'] = f"{'+' if line_diff > 0 else ''}{line_diff} lines"
                
                # Use pattern matcher to detect functions
                language = self._detect_language(file_path)
                current_functions = set(self.pattern_matcher.extract_functions(current_content, language))
                previous_functions = set(self.pattern_matcher.extract_functions(previous_content, language))
                functions_added = list(current_functions - previous_functions)
                
                if functions_added:
                    details['functions_added'] = functions_added
                
                # Update cache
                self.file_contents_cache[file_path] = current_content
                
        except Exception as e:
            details['error'] = f"Could not analyze: {str(e)}"
            
        return details
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        return self.scoring_system._detect_language(file_path)
    
    def _calculate_change_score(self, file_path: str, details: Dict[str, Any]) -> int:
        """Calculate score for a file change"""
        try:
            if not os.path.exists(file_path):
                return 1  # Base score for deletion
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Use scoring system to calculate score
            score = self.scoring_system.calculate_change_score(content, file_path)
            
            # Bonus for new functions (already detected)
            if 'functions_added' in details and details['functions_added']:
                score += len(details['functions_added']) * 2
                
            # Penalty for very small changes
            if 'lines_changed' in details:
                lines_str = details['lines_changed']
                if 'lines' in lines_str:
                    try:
                        lines_num = int(lines_str.split()[0].replace('+', '').replace('-', ''))
                        if lines_num <= 2:
                            score = max(0, score - 1)
                    except:
                        pass
            
            return max(0, score)
            
        except Exception as e:
            self._log_error(f"Error calculating score for {file_path}: {e}")
            return 1  # Default score
    
    def _should_trigger_processing(self) -> bool:
        """Score-based decision logic for when to trigger navigator processing"""
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
            self._log_debug(f"Score threshold reached: {self.buffer_score} >= {self.score_threshold}")
            return True
            
        # 2. Idle threshold exceeded (secondary trigger)
        idle_time = current_time - self.last_activity_time
        if idle_time >= self.idle_threshold and buffer_size > 0:
            self._log_debug(f"Idle threshold reached: {idle_time:.1f}s >= {self.idle_threshold}s")
            return True
            
        # 3. Legacy conditions for backward compatibility
        if self._has_function_completion() or self._has_architectural_change():
            return True
            
        # 4. Buffer size fallback
        if buffer_size >= self.buffer_threshold:
            return True
            
        return False
    
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
            self._log_debug(f"Cleaned {initial_size - len(self.change_buffer)} old entries, score now {self.buffer_score}")
    
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
    
    def _has_sustained_activity(self) -> bool:
        """Check for sustained activity across multiple files"""
        if len(self.change_buffer) < 3:
            return False
            
        # Check if we have changes across multiple files
        unique_files = set(event.file_path for event in self.change_buffer)
        
        # Check time span of recent activity  
        if len(self.change_buffer) >= 2:
            time_span = (self.change_buffer[-1].timestamp - self.change_buffer[0].timestamp).total_seconds()
            # If we have 3+ files changed in less than 5 minutes, that's sustained activity
            return len(unique_files) >= 3 and time_span < 300
            
        return False
    
    def _has_high_priority_patterns(self) -> bool:
        """Check if buffer contains high-priority patterns"""
        for event in self.change_buffer:
            if event.score >= 4:  # High individual score
                return True
        return False
    
    def _trigger_navigator_processing(self):
        """Send accumulated changes to navigator for processing"""
        if self.navigator:
            changes_summary = self._get_changes_summary()
            
            # Add decision context for the Navigator
            changes_summary['processing_reason'] = self._get_processing_reason()
            changes_summary['priority_level'] = self._assess_priority_level()
            changes_summary['buffer_score'] = self.buffer_score
            changes_summary['score_breakdown'] = self._get_score_breakdown()
            
            self.navigator.process_changes(changes_summary)
            
            # Update last processing time
            self.last_processing_time = time.time()
            
            # Clear buffer and reset score
            self._clear_buffer()
    
    def _get_processing_reason(self) -> str:
        """Determine why we're processing now (for Navigator context)"""
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
        elif self._has_sustained_activity():
            return 'sustained_activity'
        else:
            return 'threshold_met'
    
    def _assess_priority_level(self) -> str:
        """Assess priority level based on buffer score and content"""
        # High priority: high score or critical patterns
        if self.buffer_score >= self.score_threshold * 1.5 or self._has_high_priority_patterns():
            return 'high'
        
        # Medium priority: moderate score or function completion
        if self.buffer_score >= self.score_threshold or self._has_function_completion():
            return 'medium'
            
        # Low priority: low score changes
        return 'low'
    
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
        self._log_debug("Buffer cleared, score reset to 0")
    
    def _display_change(self, change_event: ChangeEvent):
        """Display file change to terminal with color coding"""
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
            level = 'success'
        elif change_event.event_type == 'modified':
            icon = '~'
            level = 'info'
        else:  # deleted
            icon = '-'
            level = 'error'
        
        message = f"{icon} File {file_name} {change_event.event_type}{details_str}"
        self._log(message, level)
    
    def get_status(self) -> Dict[str, Any]:
        """Get observer agent status"""
        base_status = super().get_status()
        base_status.update({
            'directory_path': self.directory_path,
            'monitoring': self.running,
            'buffer_size': len(self.change_buffer),
            'buffer_score': self.buffer_score,
            'last_activity': datetime.fromtimestamp(self.last_activity_time).isoformat() if self.last_activity_time else None,
            'score_threshold': self.score_threshold,
            'idle_threshold': self.idle_threshold
        })
        return base_status