"""
Comprehensive error handling and fallback mechanisms for Blue CLI.
"""

import asyncio
import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, Dict, List
from pathlib import Path

from termcolor import colored


class BlueError(Exception):
    """Base exception for Blue CLI errors."""
    pass


class ConfigurationError(BlueError):
    """Configuration-related errors."""
    pass


class IntegrationError(BlueError):
    """External integration errors."""
    pass


class GraphError(BlueError):
    """Workspace graph errors."""
    pass


class NavigatorError(BlueError):
    """Navigator agent errors."""
    pass


class ErrorHandler:
    """
    Centralized error handling with:
    - Graceful degradation for non-critical failures
    - User-friendly error messages
    - Detailed logging for debugging
    - Automatic retry mechanisms
    - Fallback modes for offline operation
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path.home() / '.blue-cli' / 'errors.log'
        self.setup_logging()
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.recent_errors: List[Dict[str, Any]] = []
        self.fallback_mode = False
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # Exponential backoff
    
    def setup_logging(self):
        """Setup logging configuration."""
        try:
            # Ensure log directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger('blue-cli')
            
        except Exception as e:
            print(colored(f"Warning: Could not setup logging: {e}", "yellow"))
            self.logger = logging.getLogger('blue-cli')
    
    def handle_error(self, 
                    error: Exception, 
                    context: str = "Unknown",
                    user_message: Optional[str] = None,
                    fatal: bool = False) -> bool:
        """
        Handle an error with appropriate logging and user feedback.
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            user_message: Custom message to show to user
            fatal: Whether this is a fatal error that should stop execution
            
        Returns:
            True if execution can continue, False if should stop
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Track error frequency
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Record error details
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_msg,
            'context': context,
            'traceback': traceback.format_exc(),
            'fatal': fatal
        }
        
        self.recent_errors.append(error_record)
        if len(self.recent_errors) > 50:
            self.recent_errors = self.recent_errors[-25:]
        
        # Log error
        self.logger.error(f"[{context}] {error_type}: {error_msg}")
        self.logger.debug(traceback.format_exc())
        
        # Show user-friendly message
        if user_message:
            print(colored(user_message, "red"))
        else:
            user_msg = self._get_user_friendly_message(error, context)
            print(colored(user_msg, "red"))
        
        # Check if we should enter fallback mode
        if self._should_enter_fallback(error_type):
            self._enter_fallback_mode()
        
        return not fatal
    
    def _get_user_friendly_message(self, error: Exception, context: str) -> str:
        """Generate user-friendly error messages."""
        error_type = type(error).__name__
        
        # Configuration errors
        if isinstance(error, ConfigurationError):
            return f"Configuration issue in {context}. Use --help or check your config file."
        
        # Integration errors
        elif isinstance(error, IntegrationError):
            return f"External service connection failed in {context}. Working in offline mode."
        
        # Network-related errors
        elif "Connection" in error_type or "Network" in error_type:
            return f"Network connectivity issue in {context}. Retrying with cached data."
        
        # Permission errors
        elif "Permission" in error_type:
            return f"Permission denied in {context}. Check file/directory permissions."
        
        # File not found
        elif "FileNotFound" in error_type:
            return f"Required file not found in {context}. Please check the path."
        
        # API errors
        elif "API" in error_type or "HTTP" in error_type:
            return f"External API error in {context}. Using cached data where possible."
        
        # Generic fallback
        else:
            return f"Unexpected error in {context}: {str(error)[:100]}..."
    
    def _should_enter_fallback(self, error_type: str) -> bool:
        """Determine if we should enter fallback mode based on error frequency."""
        # Enter fallback mode if we've seen too many network/API errors
        network_errors = sum(
            count for err_type, count in self.error_counts.items()
            if any(keyword in err_type.lower() for keyword in ['connection', 'network', 'http', 'api'])
        )
        
        return network_errors >= 5 and not self.fallback_mode
    
    def _enter_fallback_mode(self):
        """Enter fallback mode for offline operation."""
        self.fallback_mode = True
        print(colored("⚠️  Entering fallback mode due to connectivity issues", "yellow"))
        print(colored("   • Working with local data only", "cyan"))
        print(colored("   • External integrations disabled", "cyan"))
        print(colored("   • Use /status to check when connectivity is restored", "cyan"))
    
    def exit_fallback_mode(self):
        """Exit fallback mode."""
        if self.fallback_mode:
            self.fallback_mode = False
            print(colored("✓ Exiting fallback mode - full functionality restored", "green"))
    
    def is_fallback_mode(self) -> bool:
        """Check if currently in fallback mode."""
        return self.fallback_mode
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        total_errors = len(self.recent_errors)
        if total_errors == 0:
            return {'total': 0, 'message': 'No recent errors'}
        
        # Count by type
        error_types = {}
        for error in self.recent_errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Get most common error
        most_common = max(error_types.items(), key=lambda x: x[1])
        
        return {
            'total': total_errors,
            'types': error_types,
            'most_common': most_common,
            'fallback_mode': self.fallback_mode,
            'recent': self.recent_errors[-5:]  # Last 5 errors
        }


def with_error_handling(context: str = "Operation", 
                       user_message: Optional[str] = None,
                       fatal: bool = False,
                       retry: bool = False):
    """
    Decorator for automatic error handling.
    
    Args:
        context: Context description for error logging
        user_message: Custom user message on error
        fatal: Whether errors should be fatal
        retry: Whether to retry on failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = getattr(args[0], 'error_handler', None) if args else None
            if not error_handler:
                error_handler = ErrorHandler()
            
            retries = 3 if retry else 1
            last_error = None
            
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if attempt < retries - 1:
                        delay = [1, 2, 5][attempt]
                        print(colored(f"Retrying {context} in {delay}s... (attempt {attempt + 2}/{retries})", "yellow"))
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        can_continue = error_handler.handle_error(
                            e, context, user_message, fatal
                        )
                        if not can_continue:
                            raise
                        return None
            
            return None
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = getattr(args[0], 'error_handler', None) if args else None
            if not error_handler:
                error_handler = ErrorHandler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                can_continue = error_handler.handle_error(
                    e, context, user_message, fatal
                )
                if not can_continue:
                    raise
                return None
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_async_run(coro, error_handler: Optional[ErrorHandler] = None, context: str = "Async operation"):
    """Safely run an async coroutine with error handling."""
    if not error_handler:
        error_handler = ErrorHandler()
    
    try:
        return asyncio.run(coro)
    except Exception as e:
        error_handler.handle_error(e, context)
        return None


def validate_file_path(path: str, must_exist: bool = True) -> Path:
    """Validate and return a Path object with error handling."""
    try:
        path_obj = Path(path).resolve()
        
        if must_exist and not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        return path_obj
    
    except Exception as e:
        raise ConfigurationError(f"Invalid file path '{path}': {e}")


def validate_url(url: str) -> str:
    """Validate URL format."""
    import re
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ConfigurationError(f"Invalid URL format: {url}")
    
    return url


class HealthChecker:
    """System health monitoring and diagnostics."""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Check disk space
        try:
            import shutil
            disk_usage = shutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            
            health_report['checks']['disk_space'] = {
                'status': 'ok' if free_gb > 1 else 'warning',
                'free_gb': round(free_gb, 2),
                'message': f"{free_gb:.1f} GB free" if free_gb > 1 else "Low disk space"
            }
        except Exception as e:
            health_report['checks']['disk_space'] = {
                'status': 'error',
                'message': str(e)
            }
        
        # Check Python dependencies
        try:
            import autogen, watchdog, requests, networkx, termcolor, tomli
            health_report['checks']['dependencies'] = {
                'status': 'ok',
                'message': 'All required packages available'
            }
        except ImportError as e:
            health_report['checks']['dependencies'] = {
                'status': 'error',
                'message': f"Missing dependency: {e}"
            }
        
        # Check network connectivity
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            health_report['checks']['network'] = {
                'status': 'ok',
                'message': 'Network connectivity available'
            }
        except Exception:
            health_report['checks']['network'] = {
                'status': 'warning',
                'message': 'Network connectivity issues detected'
            }
        
        # Check error frequency
        error_summary = self.error_handler.get_error_summary()
        if error_summary['total'] > 10:
            health_report['checks']['error_rate'] = {
                'status': 'warning',
                'message': f"High error rate: {error_summary['total']} recent errors"
            }
        else:
            health_report['checks']['error_rate'] = {
                'status': 'ok',
                'message': f"{error_summary['total']} recent errors"
            }
        
        # Determine overall status
        statuses = [check['status'] for check in health_report['checks'].values()]
        if 'error' in statuses:
            health_report['overall_status'] = 'unhealthy'
        elif 'warning' in statuses:
            health_report['overall_status'] = 'degraded'
        
        return health_report
    
    def print_health_report(self, report: Dict[str, Any]):
        """Print a formatted health report."""
        status_colors = {
            'healthy': 'green',
            'degraded': 'yellow',
            'unhealthy': 'red'
        }
        
        check_colors = {
            'ok': 'green',
            'warning': 'yellow',
            'error': 'red'
        }
        
        print(colored("=== System Health Report ===", "cyan"))
        print(colored(f"Overall Status: {report['overall_status'].upper()}", 
                     status_colors.get(report['overall_status'], 'white')))
        print()
        
        for check_name, check_info in report['checks'].items():
            status = check_info['status']
            message = check_info['message']
            color = check_colors.get(status, 'white')
            
            print(colored(f"{check_name.replace('_', ' ').title()}: {status.upper()}", color))
            print(colored(f"  {message}", 'white'))
        
        print(colored(f"\nReport generated: {report['timestamp']}", 'cyan'))