"""
Scoring System

Handles pattern-based scoring of code changes to determine comment priority.
"""

import re
from typing import Dict, Any, List
from pathlib import Path


class ScoringSystem:
    """Handles pattern-based scoring of code changes"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scoring_config = config.get('scoring', {})
    
    def calculate_change_score(self, content: str, file_path: str) -> int:
        """Calculate score for code changes based on patterns"""
        language = self._detect_language(file_path)
        score = 0
        
        # Score different types of patterns
        pattern_categories = [
            'function_patterns',
            'import_patterns', 
            'security_patterns',
            'error_patterns',
            'test_patterns',
            'minor_patterns'
        ]
        
        for category in pattern_categories:
            patterns = self.scoring_config.get(category, [])
            score += self._score_content_patterns(content, patterns, language)
        
        return max(0, score)  # Ensure non-negative score
    
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
    
    def _score_content_patterns(self, content: str, patterns: List[Dict[str, Any]], file_language: str) -> int:
        """Score content based on configured patterns"""
        total_score = 0
        
        for pattern_config in patterns:
            pattern = pattern_config.get('pattern', '')
            points = pattern_config.get('points', 0)
            pattern_language = pattern_config.get('language', 'all')
            
            # Check language compatibility
            if pattern_language != 'all' and pattern_language != file_language:
                continue
            
            # Count pattern occurrences
            try:
                matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
                total_score += matches * points
            except re.error:
                # Skip invalid regex patterns
                continue
        
        return total_score
    
    def get_change_priority(self, score: int, threshold: int) -> str:
        """Determine priority level based on score"""
        if score >= threshold + 5:
            return 'high'
        elif score >= threshold:
            return 'medium'
        else:
            return 'low'
    
    def analyze_change_details(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze change details for scoring context"""
        language = self._detect_language(file_path)
        
        analysis = {
            'language': language,
            'line_count': len(content.split('\n')),
            'has_functions': False,
            'has_classes': False,
            'has_imports': False,
            'has_security_keywords': False,
            'has_error_handling': False,
            'has_tests': False
        }
        
        # Detect specific patterns
        function_patterns = {
            'python': [r'def\s+\w+', r'class\s+\w+'],
            'javascript': [r'function\s+\w+', r'const\s+\w+\s*=\s*\(', r'=>\s*{'],
            'java': [r'public\s+\w+', r'private\s+\w+', r'class\s+\w+'],
            'go': [r'func\s+\w+']
        }
        
        if language in function_patterns:
            for pattern in function_patterns[language]:
                if re.search(pattern, content, re.IGNORECASE):
                    analysis['has_functions'] = True
                    break
        
        # Check for imports
        import_patterns = [r'import\s+', r'from\s+\w+\s+import', r'#include', r'require\s*\(']
        analysis['has_imports'] = any(re.search(pattern, content, re.IGNORECASE) for pattern in import_patterns)
        
        # Check for security keywords
        security_keywords = ['password', 'auth', 'token', 'encrypt', 'hash', 'sql', 'query']
        analysis['has_security_keywords'] = any(keyword in content.lower() for keyword in security_keywords)
        
        # Check for error handling
        error_patterns = [r'try\s*:', r'except\s+', r'catch\s*\(', r'throw\s+', r'error']
        analysis['has_error_handling'] = any(re.search(pattern, content, re.IGNORECASE) for pattern in error_patterns)
        
        # Check for tests
        test_patterns = [r'test_\w+', r'def\s+test', r'it\s*\(', r'describe\s*\(', r'assert\s+']
        analysis['has_tests'] = any(re.search(pattern, content, re.IGNORECASE) for pattern in test_patterns)
        
        return analysis