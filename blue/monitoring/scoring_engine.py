"""
Scoring Engine

Pure pattern-based scoring system for code changes. No intelligence,
just mechanical pattern matching and point assignment.
"""

import re
from typing import Dict, Any, List
from pathlib import Path


class ScoringEngine:
    """Handles pattern-based scoring of code changes"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scoring_config = config.get('scoring', {})
    
    def calculate_change_score(self, content: str, file_path: str) -> int:
        """Calculate score for code changes based on patterns"""
        language = self._detect_language(file_path)
        score = 0
        
        # Base score for any change
        score += 1
        
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
            category_score = self._score_content_patterns(content, patterns, language)
            score += category_score
            
            # Debug output for significant scores
            if category_score > 0:
                print(f"[DEBUG] {category}: +{category_score} points")
        
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
                # For security and minor patterns, use simple substring matching
                if any(cat in ['security', 'minor'] for cat in pattern.lower().split()):
                    matches = content.lower().count(pattern.lower())
                else:
                    # For structural patterns, use regex
                    matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
                
                if matches > 0:
                    pattern_score = matches * points
                    total_score += pattern_score
                    
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
    
    def analyze_score_breakdown(self, content: str, file_path: str) -> Dict[str, Any]:
        """Get detailed breakdown of how score was calculated"""
        language = self._detect_language(file_path)
        breakdown = {
            'total_score': 0,
            'language': language,
            'category_scores': {},
            'pattern_matches': []
        }
        
        # Base score
        breakdown['total_score'] += 1
        breakdown['category_scores']['base'] = 1
        
        # Score each category
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
            category_score = 0
            category_matches = []
            
            for pattern_config in patterns:
                pattern = pattern_config.get('pattern', '')
                points = pattern_config.get('points', 0)
                pattern_language = pattern_config.get('language', 'all')
                
                # Check language compatibility
                if pattern_language != 'all' and pattern_language != language:
                    continue
                
                # Count matches
                try:
                    if any(cat in ['security', 'minor'] for cat in category.lower().split()):
                        matches = content.lower().count(pattern.lower())
                    else:
                        matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
                    
                    if matches > 0:
                        pattern_score = matches * points
                        category_score += pattern_score
                        category_matches.append({
                            'pattern': pattern,
                            'matches': matches,
                            'points_each': points,
                            'total_points': pattern_score
                        })
                        
                except re.error:
                    continue
            
            if category_score > 0:
                breakdown['category_scores'][category] = category_score
                breakdown['pattern_matches'].extend(category_matches)
                breakdown['total_score'] += category_score
        
        return breakdown
    
    def get_scoring_config(self) -> Dict[str, Any]:
        """Get the current scoring configuration"""
        return self.scoring_config.copy()
    
    def update_scoring_config(self, new_config: Dict[str, Any]):
        """Update the scoring configuration"""
        self.scoring_config.update(new_config)