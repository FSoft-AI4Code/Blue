"""
File Monitor Utilities

Provides utilities for file system monitoring and change detection.
"""

import os
from pathlib import Path
from typing import List, Set, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileMonitor:
    """Utilities for file monitoring configuration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
    
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


class BlueFileSystemEventHandler(FileSystemEventHandler):
    """Custom file system event handler for Blue"""
    
    def __init__(self, file_monitor: FileMonitor, callback):
        super().__init__()
        self.file_monitor = file_monitor
        self.callback = callback
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        if self.file_monitor.should_monitor_file(event.src_path):
            self.callback('modified', event.src_path)
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        if self.file_monitor.should_monitor_file(event.src_path):
            self.callback('created', event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if event.is_directory:
            return
        
        # Note: We can't check if deleted file should be monitored since it's gone
        # So we'll let the callback decide
        self.callback('deleted', event.src_path)
    
    def on_moved(self, event):
        """Handle file move events"""
        if event.is_directory:
            return
        
        # Check both source and destination paths
        src_monitored = self.file_monitor.should_monitor_file(event.src_path)
        dest_monitored = self.file_monitor.should_monitor_file(event.dest_path)
        
        if src_monitored or dest_monitored:
            self.callback('moved', event.src_path, event.dest_path)