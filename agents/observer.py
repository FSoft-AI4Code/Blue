"""
Observer Agent - Event-driven directory watching and remote context monitoring.
"""

import asyncio
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import concurrent.futures

import requests
from termcolor import colored


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events for the Observer Agent."""
    
    def __init__(self, callback: Callable[[Dict[str, Any]], None], loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__()
        self.callback = callback
        self.loop = loop
        self.ignored_patterns = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.vscode', '.idea', '.blue_state.json'
        }
        self.watched_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.clj', '.hs', '.ml', '.elm', '.dart'
        }
    
    def should_ignore(self, path: str) -> bool:
        """Check if file/directory should be ignored."""
        path_obj = Path(path)
        
        # Check ignored patterns
        for pattern in self.ignored_patterns:
            if pattern in path_obj.parts:
                return True
        
        # For files, check extension
        if path_obj.is_file():
            return path_obj.suffix not in self.watched_extensions
        
        return False
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self._emit_event('modified', event.src_path)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self._emit_event('created', event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if not event.is_directory and not self.should_ignore(event.src_path):
            self._emit_event('deleted', event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events."""
        if hasattr(event, 'dest_path') and not event.is_directory:
            if not self.should_ignore(event.src_path) or not self.should_ignore(event.dest_path):
                self._emit_event('moved', event.src_path, event.dest_path)
    
    def _emit_event(self, event_type: str, src_path: str, dest_path: Optional[str] = None):
        """Emit processed event to callback."""
        try:
            event_data = {
                'type': event_type,
                'src_path': src_path,
                'dest_path': dest_path,
                'timestamp': datetime.now().isoformat(),
                'file_info': self._get_file_info(src_path) if os.path.exists(src_path) else None
            }
            
            # Simplified event information
            print(colored(f"📄 {event_type.upper()}: {os.path.basename(src_path)}", "yellow"))
            
            # Schedule callback on the main event loop if available
            if self.loop and not self.loop.is_closed():
                try:
                    print(colored(f"🔧 Scheduling callback for {event_type} - {os.path.basename(src_path)}", "blue"))
                    print(colored(f"📞 Loop available, scheduling callback", "cyan"))
                    
                    # Use run_coroutine_threadsafe for proper async execution
                    future = asyncio.run_coroutine_threadsafe(self._async_callback(event_data), self.loop)
                    
                    def handle_result(fut):
                        try:
                            result = fut.result()
                            print(colored(f"🎉 Callback execution completed", "green"))
                        except Exception as e:
                            print(colored(f"🚫 Callback execution failed: {e}", "red"))
                    
                    future.add_done_callback(handle_result)
                    print(colored(f"✅ Callback scheduled successfully", "green"))
                    
                except RuntimeError as e:
                    print(colored(f"Event loop error: {e}", "red"))
                except Exception as e:
                    print(colored(f"Callback scheduling error: {e}", "red"))
            else:
                print(colored(f"❌ No event loop available (loop: {self.loop}, closed: {self.loop.is_closed() if self.loop else 'None'})", "red"))
            
        except Exception as e:
            print(colored(f"Error processing file event: {e}", "red"))
    
    async def _async_callback(self, event_data: Dict[str, Any]):
        """Async wrapper for callback."""
        try:
            print(colored(f"🎯 Executing async callback for {event_data.get('type', 'unknown')}", "green"))
            
            # Check if callback is async or sync
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(event_data)
            else:
                # Call sync callback directly
                self.callback(event_data)
                
            print(colored(f"✅ Callback completed successfully", "green"))
        except Exception as e:
            print(colored(f"Error in event callback: {e}", "red"))
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get relevant file information for the event."""
        try:
            path_obj = Path(file_path)
            stat = path_obj.stat()
            
            info = {
                'name': path_obj.name,
                'extension': path_obj.suffix,
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # Add content hash for small files
            if stat.st_size < 50000:  # 50KB limit
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        info['content_hash'] = hashlib.md5(content).hexdigest()
                except:
                    pass
            
            return info
            
        except Exception as e:
            return {'error': str(e)}


class ObserverAgent:
    """
    Observer Agent handles:
    - Event-driven directory watching with watchdog
    - Remote context monitoring (APIs, webhooks)
    - Event processing and notification to Navigator
    - Caching and offline fallback
    """
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[FileEventHandler] = None
        self.change_callback: Optional[Callable] = None
        
        # Remote monitoring state
        self.remote_sources: Dict[str, Dict[str, Any]] = {}
        self.remote_cache: Dict[str, Dict[str, Any]] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Event buffer for batching
        self.event_buffer: List[Dict[str, Any]] = []
        self.buffer_size = 10
        self.buffer_timeout = 5.0  # seconds
        self.last_buffer_flush = datetime.now()
        
        # Simplified event handling
        self.debug_mode = False
    
    async def start_watching(self, change_callback: Callable[[Dict[str, Any]], None]):
        """Start watching the workspace directory for changes."""
        self.change_callback = change_callback
        
        try:
            # Get current event loop
            current_loop = asyncio.get_running_loop()
            
            # Initialize file system watcher with event loop reference
            self.event_handler = FileEventHandler(self._on_file_event, current_loop)
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                str(self.workspace_dir),
                recursive=True
            )
            self.observer.start()
            
            # Start remote monitoring task
            self.monitoring_task = asyncio.create_task(self._monitor_remote_sources())
            
            print(colored(f"Observer started watching: {self.workspace_dir}", "green"))
            
        except Exception as e:
            print(colored(f"Error starting observer: {e}", "red"))
            raise
    
    async def stop_watching(self):
        """Stop watching and clean up resources."""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Flush any remaining events
            await self._flush_event_buffer()
            
            print(colored("Observer stopped", "green"))
            
        except Exception as e:
            print(colored(f"Error stopping observer: {e}", "red"))
    
    async def add_remote_source(self, source_type: str, config: Dict[str, Any]) -> bool:
        """Add a remote source for monitoring (Jira, GitHub, etc.)."""
        try:
            source_id = f"{source_type}_{len(self.remote_sources)}"
            
            self.remote_sources[source_id] = {
                'type': source_type,
                'config': config,
                'last_check': None,
                'last_data': None,
                'error_count': 0
            }
            
            # Initial fetch
            await self._fetch_remote_source(source_id)
            
            print(colored(f"Added remote source: {source_type}", "green"))
            return True
            
        except Exception as e:
            print(colored(f"Error adding remote source: {e}", "red"))
            return False
    
    async def _on_file_event(self, event_data: Dict[str, Any]):
        """Handle file system events."""
        print(colored(f"🔥 Main handler received event: {event_data.get('type', 'unknown')}", "magenta"))
        
        # Add to buffer
        self.event_buffer.append(event_data)
        
        # Check if buffer should be flushed
        now = datetime.now()
        time_since_flush = (now - self.last_buffer_flush).total_seconds()
        
        if len(self.event_buffer) >= self.buffer_size or time_since_flush >= self.buffer_timeout:
            await self._flush_event_buffer()
    
    async def _flush_event_buffer(self):
        """Flush the event buffer and notify callback."""
        if not self.event_buffer or not self.change_callback:
            return
        
        try:
            # Process events in buffer
            processed_events = await self._process_event_batch(self.event_buffer.copy())
            
            # Send to callback if significant
            if processed_events:
                await self.change_callback(processed_events)
            
            # Clear buffer
            self.event_buffer.clear()
            self.last_buffer_flush = datetime.now()
            
        except Exception as e:
            print(colored(f"Error flushing event buffer: {e}", "red"))
    
    async def _process_event_batch(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process a batch of events and determine significance."""
        if not events:
            return None
        
        # Aggregate event information
        file_counts = {}
        event_types = {}
        affected_files = []
        
        for event in events:
            # Count events by file
            file_path = event.get('src_path', '')
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
            
            # Count event types
            event_type = event.get('type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Track affected files
            if file_path and file_path not in affected_files:
                affected_files.append(file_path)
        
        # Calculate significance score
        significance_score = 0
        
        # Structural changes get higher scores
        if event_types.get('created', 0) > 0:
            significance_score += 2
        if event_types.get('deleted', 0) > 0:
            significance_score += 2
        if event_types.get('moved', 0) > 0:
            significance_score += 1
        
        # Multiple file changes
        if len(affected_files) > 1:
            significance_score += min(len(affected_files), 3)
        
        # Rapid changes to same file (potential complexity increase)
        for count in file_counts.values():
            if count > 2:
                significance_score += 1
        
        # Only return if significant enough
        if significance_score < 2:
            return None
        
        return {
            'batch_info': {
                'event_count': len(events),
                'affected_files': affected_files[:5],  # Limit to 5 files
                'event_types': event_types,
                'significance_score': significance_score,
                'time_span': {
                    'start': events[0]['timestamp'],
                    'end': events[-1]['timestamp']
                }
            },
            'raw_events': events
        }
    
    async def _monitor_remote_sources(self):
        """Background task to monitor remote sources."""
        while True:
            try:
                for source_id in list(self.remote_sources.keys()):
                    try:
                        await self._fetch_remote_source(source_id)
                    except Exception as e:
                        print(colored(f"Error fetching {source_id}: {e}", "yellow"))
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(colored(f"Error in remote monitoring: {e}", "red"))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _fetch_remote_source(self, source_id: str):
        """Fetch data from a remote source."""
        source = self.remote_sources.get(source_id)
        if not source:
            return
        
        source_type = source['type']
        config = source['config']
        
        try:
            if source_type == 'jira':
                data = await self._fetch_jira(config)
            elif source_type == 'github':
                data = await self._fetch_github(config)
            elif source_type == 'gdrive':
                data = await self._fetch_gdrive(config)
            else:
                print(colored(f"Unknown source type: {source_type}", "yellow"))
                return
            
            # Check for changes
            if source['last_data'] != data:
                # Data changed, notify callback
                change_event = {
                    'type': 'remote_change',
                    'source_id': source_id,
                    'source_type': source_type,
                    'old_data': source['last_data'],
                    'new_data': data,
                    'timestamp': datetime.now().isoformat()
                }
                
                if self.change_callback:
                    await self.change_callback(change_event)
                
                source['last_data'] = data
            
            source['last_check'] = datetime.now().isoformat()
            source['error_count'] = 0
            
            # Update cache
            self.remote_cache[source_id] = data
            
        except Exception as e:
            source['error_count'] += 1
            print(colored(f"Error fetching {source_type} ({source_id}): {e}", "yellow"))
            
            # Use cached data if available
            if source_id in self.remote_cache:
                print(colored(f"Using cached data for {source_id}", "cyan"))
    
    async def _fetch_jira(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from Jira API."""
        # Placeholder implementation
        # In real implementation, would use Jira REST API
        return {
            'tickets': [],
            'last_updated': datetime.now().isoformat()
        }
    
    async def _fetch_github(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from GitHub API."""
        # Placeholder implementation
        # In real implementation, would use GitHub REST/GraphQL API
        return {
            'issues': [],
            'pull_requests': [],
            'commits': [],
            'last_updated': datetime.now().isoformat()
        }
    
    async def _fetch_gdrive(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from Google Drive API."""
        # Placeholder implementation
        # In real implementation, would use Google Drive API
        return {
            'documents': [],
            'last_updated': datetime.now().isoformat()
        }
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'watching_directory': str(self.workspace_dir) if self.workspace_dir else None,
            'observer_active': self.observer is not None and self.observer.is_alive(),
            'remote_sources': len(self.remote_sources),
            'event_buffer_size': len(self.event_buffer),
            'cache_entries': len(self.remote_cache)
        }