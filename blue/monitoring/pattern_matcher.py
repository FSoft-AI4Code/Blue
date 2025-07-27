"""
Pattern Matching Utilities

Provides utilities for pattern matching and code analysis.
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class PatternMatcher:
    """Utilities for pattern matching in code"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scoring_config = config.get('scoring', {})
    
    def extract_functions(self, content: str, language: str) -> List[str]:
        """Extract function names from code content"""
        function_patterns = {
            'python': r'def\s+(\w+)\s*\(',
            'javascript': r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*{|function))',
            'java': r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{',
            'go': r'func\s+(\w+)\s*\(',
            'c': r'(?:static\s+)?[\w*]+\s+(\w+)\s*\([^)]*\)\s*\{'
        }
        
        pattern = function_patterns.get(language.lower())
        if not pattern:
            return []
        
        matches = re.findall(pattern, content, re.MULTILINE)
        # Handle tuples from complex regex groups
        functions = []
        for match in matches:
            if isinstance(match, tuple):
                functions.extend([m for m in match if m])
            else:
                functions.append(match)
        
        return functions
    
    def extract_classes(self, content: str, language: str) -> List[str]:
        """Extract class names from code content"""
        class_patterns = {
            'python': r'class\s+(\w+)(?:\([^)]*\))?:',
            'javascript': r'class\s+(\w+)(?:\s+extends\s+\w+)?',
            'java': r'(?:public|private|protected|\s)*class\s+(\w+)',
            'go': r'type\s+(\w+)\s+struct'
        }
        
        pattern = class_patterns.get(language.lower())
        if not pattern:
            return []
        
        return re.findall(pattern, content, re.MULTILINE)
    
    def extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements from code content"""
        import_patterns = {
            'python': [
                r'import\s+([\w.]+)',
                r'from\s+([\w.]+)\s+import'
            ],
            'javascript': [
                r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ],
            'java': [
                r'import\s+([\w.]+);'
            ],
            'go': [
                r'import\s+[\'"]([^\'"]+)[\'"]',
                r'import\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ],
            'c': [
                r'#include\s*[<"]([\w./]+)[>"]'
            ]
        }
        
        patterns = import_patterns.get(language.lower(), [])
        imports = []
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
        
        return imports
    
    def detect_code_patterns(self, content: str, language: str) -> Dict[str, Any]:
        """Detect various code patterns and return analysis"""
        analysis = {
            'functions': self.extract_functions(content, language),
            'classes': self.extract_classes(content, language),
            'imports': self.extract_imports(content, language),
            'has_main': self._has_main_function(content, language),
            'has_tests': self._has_test_patterns(content, language),
            'has_error_handling': self._has_error_handling(content, language),
            'has_security_patterns': self._has_security_patterns(content),
            'complexity_indicators': self._get_complexity_indicators(content, language)
        }
        
        return analysis
    
    def _has_main_function(self, content: str, language: str) -> bool:
        """Check if content has a main function"""
        main_patterns = {
            'python': r'if\s+__name__\s*==\s*[\'"]__main__[\'"]',
            'java': r'public\s+static\s+void\s+main\s*\(',
            'c': r'int\s+main\s*\(',
            'go': r'func\s+main\s*\('
        }
        
        pattern = main_patterns.get(language.lower())
        if not pattern:
            return False
        
        return bool(re.search(pattern, content, re.MULTILINE))
    
    def _has_test_patterns(self, content: str, language: str) -> bool:
        """Check if content has test patterns"""
        test_patterns = [
            r'test_\w+',           # Python test functions
            r'def\s+test',         # Python test functions
            r'it\s*\(',            # JavaScript/Jest tests
            r'describe\s*\(',      # JavaScript/Jest test suites
            r'assert\s+',          # Generic assertions
            r'@Test',              # Java annotations
            r'func\s+Test\w+'      # Go test functions
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in test_patterns)
    
    def _has_error_handling(self, content: str, language: str) -> bool:
        """Check if content has error handling patterns"""
        error_patterns = [
            r'try\s*:',            # Python try
            r'except\s+',          # Python except
            r'catch\s*\(',         # JavaScript/Java catch
            r'throw\s+',           # Generic throw
            r'raise\s+',           # Python raise
            r'panic\s*\(',         # Go panic
            r'recover\s*\(',       # Go recover
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in error_patterns)
    
    def _has_security_patterns(self, content: str) -> bool:
        """Check if content has security-related patterns"""
        security_keywords = [
            'password', 'passwd', 'pwd',
            'auth', 'authenticate', 'authorization',
            'token', 'jwt', 'oauth',
            'encrypt', 'decrypt', 'cipher',
            'hash', 'sha', 'md5',
            'sql', 'query', 'database',
            'session', 'cookie',
            'cors', 'csrf',
            'sanitize', 'validate'
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in security_keywords)
    
    def _get_complexity_indicators(self, content: str, language: str) -> Dict[str, int]:
        """Get complexity indicators from code"""
        indicators = {
            'line_count': len(content.split('\n')),
            'function_count': len(self.extract_functions(content, language)),
            'class_count': len(self.extract_classes(content, language)),
            'import_count': len(self.extract_imports(content, language)),
            'comment_lines': len(re.findall(r'^\s*(?:#|//|/\*|\*)', content, re.MULTILINE)),
            'blank_lines': len(re.findall(r'^\s*$', content, re.MULTILINE))
        }
        
        # Calculate code density
        total_lines = indicators['line_count']
        code_lines = total_lines - indicators['comment_lines'] - indicators['blank_lines']
        indicators['code_density'] = code_lines / max(total_lines, 1)
        
        return indicators