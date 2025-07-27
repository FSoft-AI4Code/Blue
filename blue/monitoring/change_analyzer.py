"""
Change Analyzer

Analyzes individual file changes for meaningful content, detects functions,
calculates scores, and creates structured change events.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .pattern_matcher import PatternMatcher
from .scoring_engine import ScoringEngine


class ChangeEvent:
    """Represents a file system change event with metadata and scoring"""
    
    def __init__(self, file_path: str, event_type: str, timestamp: datetime, details: Dict[str, Any] = None):
        self.file_path = file_path
        self.event_type = event_type  # 'modified', 'created', 'deleted'
        self.timestamp = timestamp
        self.details = details or {}
        self.score = 0  # Will be calculated by analyzer
        
    def __str__(self):
        return f"{self.event_type.capitalize()} {self.file_path} at {self.timestamp.strftime('%H:%M:%S')}"


class ChangeAnalyzer:
    """Analyzes file changes to extract meaningful information and calculate scores"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pattern_matcher = PatternMatcher(config)
        self.scoring_engine = ScoringEngine(config)
        self.file_contents_cache = {}
    
    def analyze_change(self, file_path: str, event_type: str) -> Optional[ChangeEvent]:
        """Analyze a file change and return a ChangeEvent with score and details"""
        timestamp = datetime.now()
        
        # Analyze the change for meaningful content
        details = self._analyze_file_details(file_path, event_type)
        
        # Create change event
        change_event = ChangeEvent(file_path, event_type, timestamp, details)
        
        # Calculate score for this change
        change_event.score = self._calculate_change_score(file_path, details)
        
        return change_event
    
    def _analyze_file_details(self, file_path: str, event_type: str) -> Dict[str, Any]:
        """Analyze the file change for meaningful content"""
        details = {}
        
        if event_type == 'deleted':
            details['lines_changed'] = 'File deleted'
            # Remove from cache if it exists
            self.file_contents_cache.pop(file_path, None)
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
                
                # Detect language and analyze patterns
                language = self._detect_language(file_path)
                details['language'] = language
                
                # Use pattern matcher to detect functions
                current_functions = set(self.pattern_matcher.extract_functions(current_content, language))
                previous_functions = set(self.pattern_matcher.extract_functions(previous_content, language))
                functions_added = list(current_functions - previous_functions)
                
                if functions_added:
                    details['functions_added'] = functions_added
                
                # Detect other patterns
                patterns = self.pattern_matcher.detect_code_patterns(current_content, language)
                if patterns['has_security_patterns']:
                    details['has_security'] = True
                if patterns['has_error_handling']:
                    details['has_error_handling'] = True
                if patterns['has_tests']:
                    details['has_tests'] = True
                
                # Update cache
                self.file_contents_cache[file_path] = current_content
                
        except Exception as e:
            details['error'] = f"Could not analyze: {str(e)}"
            
        return details
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        suffix = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript',
            '.jsx': 'javascript',
            '.tsx': 'javascript',
            '.java': 'java',
            '.cpp': 'c',
            '.c': 'c',
            '.h': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp'
        }
        
        return language_map.get(suffix, 'unknown')
    
    def _calculate_change_score(self, file_path: str, details: Dict[str, Any]) -> int:
        """Calculate score for a file change"""
        try:
            if not os.path.exists(file_path):
                return 1  # Base score for deletion
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Use scoring engine to calculate base score
            score = self.scoring_engine.calculate_change_score(content, file_path)
            
            # Bonus for new functions (already detected in details)
            if 'functions_added' in details and details['functions_added']:
                score += len(details['functions_added']) * 2
            
            # Bonus for security patterns
            if details.get('has_security', False):
                score += 3
            
            # Bonus for error handling
            if details.get('has_error_handling', False):
                score += 2
            
            # Bonus for tests
            if details.get('has_tests', False):
                score += 2
                
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
            print(f"[ERROR] Error calculating score for {file_path}: {e}")
            return 1  # Default score
    
    def get_cached_content(self, file_path: str) -> Optional[str]:
        """Get cached content for a file"""
        return self.file_contents_cache.get(file_path)
    
    def clear_cache(self):
        """Clear the file contents cache"""
        self.file_contents_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_files': len(self.file_contents_cache),
            'total_size': sum(len(content) for content in self.file_contents_cache.values())
        }