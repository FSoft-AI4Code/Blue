"""
Tool Agents - Specialized agents for executing specific tasks like API calls,
code analysis, and external integrations.
"""

import asyncio
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

import requests
from termcolor import colored
# import autogen  # Temporarily disabled due to version conflicts


class APIToolAgent:
    """Tool agent for making external API calls."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Blue-CLI/1.0'
        })
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
    
    async def make_api_call(self, 
                           url: str, 
                           method: str = 'GET',
                           headers: Optional[Dict[str, str]] = None,
                           data: Optional[Dict[str, Any]] = None,
                           auth: Optional[tuple] = None) -> Dict[str, Any]:
        """Make an API call with rate limiting and error handling."""
        try:
            # Check rate limits
            domain = url.split('/')[2]
            if not await self._check_rate_limit(domain):
                return {'error': 'Rate limit exceeded', 'retry_after': 60}
            
            # Prepare request
            kwargs = {
                'url': url,
                'method': method,
                'timeout': 30
            }
            
            if headers:
                kwargs['headers'] = headers
            if data:
                if method.upper() in ['POST', 'PUT', 'PATCH']:
                    kwargs['json'] = data
                else:
                    kwargs['params'] = data
            if auth:
                kwargs['auth'] = auth
            
            # Make request
            response = self.session.request(**kwargs)
            
            # Update rate limits
            await self._update_rate_limits(domain, response.headers)
            
            # Handle response
            if response.status_code >= 400:
                return {
                    'error': f'HTTP {response.status_code}',
                    'message': response.text[:500]
                }
            
            try:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            except ValueError:
                return {
                    'success': True,
                    'data': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    async def _check_rate_limit(self, domain: str) -> bool:
        """Check if we can make a request to this domain."""
        if domain not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[domain]
        now = datetime.now().timestamp()
        
        if now < limit_info.get('reset_time', 0):
            return False
        
        return True
    
    async def _update_rate_limits(self, domain: str, headers: Dict[str, str]):
        """Update rate limit information from response headers."""
        if domain not in self.rate_limits:
            self.rate_limits[domain] = {}
        
        # GitHub-style rate limits
        if 'X-RateLimit-Remaining' in headers:
            remaining = int(headers['X-RateLimit-Remaining'])
            reset_time = int(headers.get('X-RateLimit-Reset', 0))
            
            self.rate_limits[domain].update({
                'remaining': remaining,
                'reset_time': reset_time
            })
        
        # Twitter-style rate limits
        elif 'x-rate-limit-remaining' in headers:
            remaining = int(headers['x-rate-limit-remaining'])
            reset_time = int(headers.get('x-rate-limit-reset', 0))
            
            self.rate_limits[domain].update({
                'remaining': remaining,
                'reset_time': reset_time
            })


class CodeAnalysisToolAgent:
    """Tool agent for analyzing code changes and patterns."""
    
    def __init__(self):
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
    
    async def analyze_file_changes(self, file_path: str, old_content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze changes in a code file."""
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                if old_content:
                    return {
                        'change_type': 'deleted',
                        'language': self._detect_language(path_obj.suffix),
                        'impact_score': 3  # Deletion is significant
                    }
                return {'error': 'File does not exist'}
            
            # Read current content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            except UnicodeDecodeError:
                # Binary file, skip analysis
                return {'change_type': 'binary', 'impact_score': 0}
            
            language = self._detect_language(path_obj.suffix)
            
            if old_content is None:
                # New file
                analysis = await self._analyze_code_content(current_content, language)
                analysis['change_type'] = 'created'
                analysis['impact_score'] = 2
                return analysis
            
            # Modified file - compare changes
            diff_analysis = await self._analyze_code_diff(old_content, current_content, language)
            diff_analysis['change_type'] = 'modified'
            
            return diff_analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _analyze_code_content(self, content: str, language: str) -> Dict[str, Any]:
        """Analyze code content for patterns and complexity."""
        analysis = {
            'language': language,
            'lines': len(content.split('\n')),
            'chars': len(content),
            'complexity_indicators': []
        }
        
        if language == 'python':
            return await self._analyze_python_content(content, analysis)
        elif language in ['javascript', 'typescript']:
            return await self._analyze_js_content(content, analysis)
        else:
            return await self._analyze_generic_content(content, analysis)
    
    async def _analyze_python_content(self, content: str, base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Python-specific patterns."""
        try:
            import ast
            
            tree = ast.parse(content)
            
            # Count different node types
            function_count = 0
            class_count = 0
            import_count = 0
            complexity_score = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                    complexity_score += 1
                elif isinstance(node, ast.ClassDef):
                    class_count += 1
                    complexity_score += 2
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_count += 1
                elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    complexity_score += 1
            
            base_analysis.update({
                'functions': function_count,
                'classes': class_count,
                'imports': import_count,
                'complexity_score': complexity_score
            })
            
            # Identify complexity indicators
            if complexity_score > 20:
                base_analysis['complexity_indicators'].append('high_complexity')
            if function_count > 10:
                base_analysis['complexity_indicators'].append('many_functions')
            if class_count > 3:
                base_analysis['complexity_indicators'].append('many_classes')
            
        except SyntaxError:
            base_analysis['complexity_indicators'].append('syntax_error')
        except Exception as e:
            base_analysis['parse_error'] = str(e)
        
        return base_analysis
    
    async def _analyze_js_content(self, content: str, base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript-specific patterns."""
        # Simple pattern matching for JS/TS
        function_patterns = ['function ', 'const ', 'let ', '=> ', 'async ']
        class_patterns = ['class ', 'interface ', 'type ']
        import_patterns = ['import ', 'require(', 'from ']
        
        function_count = sum(content.count(pattern) for pattern in function_patterns)
        class_count = sum(content.count(pattern) for pattern in class_patterns)
        import_count = sum(content.count(pattern) for pattern in import_patterns)
        
        complexity_score = function_count + class_count * 2
        complexity_score += content.count('if ') + content.count('for ') + content.count('while ')
        
        base_analysis.update({
            'functions': function_count,
            'classes': class_count,
            'imports': import_count,
            'complexity_score': complexity_score
        })
        
        if complexity_score > 15:
            base_analysis['complexity_indicators'].append('high_complexity')
        
        return base_analysis
    
    async def _analyze_generic_content(self, content: str, base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze generic code patterns."""
        # Basic complexity indicators
        brace_count = content.count('{') + content.count('}')
        semicolon_count = content.count(';')
        
        base_analysis.update({
            'braces': brace_count,
            'semicolons': semicolon_count,
            'complexity_score': (brace_count + semicolon_count) // 10
        })
        
        return base_analysis
    
    async def _analyze_code_diff(self, old_content: str, new_content: str, language: str) -> Dict[str, Any]:
        """Analyze differences between old and new code."""
        import difflib
        
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        # Calculate basic diff stats
        differ = difflib.SequenceMatcher(None, old_lines, new_lines)
        ratio = differ.ratio()
        
        # Count added/removed lines
        opcodes = differ.get_opcodes()
        added_lines = 0
        removed_lines = 0
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'insert':
                added_lines += j2 - j1
            elif tag == 'delete':
                removed_lines += i2 - i1
            elif tag == 'replace':
                added_lines += j2 - j1
                removed_lines += i2 - i1
        
        # Calculate impact score
        total_changes = added_lines + removed_lines
        impact_score = min(total_changes // 5, 10)  # Scale 0-10
        
        # Analyze old and new content
        old_analysis = await self._analyze_code_content(old_content, language)
        new_analysis = await self._analyze_code_content(new_content, language)
        
        return {
            'language': language,
            'similarity_ratio': ratio,
            'added_lines': added_lines,
            'removed_lines': removed_lines,
            'total_changes': total_changes,
            'impact_score': impact_score,
            'old_analysis': old_analysis,
            'new_analysis': new_analysis,
            'complexity_change': new_analysis.get('complexity_score', 0) - old_analysis.get('complexity_score', 0)
        }
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension."""
        return self.supported_languages.get(extension.lower(), 'unknown')


class GitToolAgent:
    """Tool agent for Git operations and analysis."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
    
    async def get_git_status(self) -> Dict[str, Any]:
        """Get current Git status."""
        try:
            result = await self._run_git_command(['status', '--porcelain'])
            
            if result['returncode'] != 0:
                return {'error': 'Not a git repository or git error'}
            
            # Parse git status output
            status_lines = result['stdout'].strip().split('\n') if result['stdout'].strip() else []
            
            modified = []
            added = []
            deleted = []
            untracked = []
            
            for line in status_lines:
                if len(line) < 3:
                    continue
                
                status = line[:2]
                filename = line[3:]
                
                if status.startswith('M'):
                    modified.append(filename)
                elif status.startswith('A'):
                    added.append(filename)
                elif status.startswith('D'):
                    deleted.append(filename)
                elif status.startswith('??'):
                    untracked.append(filename)
            
            return {
                'modified': modified,
                'added': added,
                'deleted': deleted,
                'untracked': untracked,
                'total_changes': len(modified) + len(added) + len(deleted) + len(untracked)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def get_recent_commits(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent commits."""
        try:
            result = await self._run_git_command([
                'log', '--oneline', f'-{count}', '--format=%H|%s|%an|%ad'
            ])
            
            if result['returncode'] != 0:
                return []
            
            commits = []
            for line in result['stdout'].strip().split('\n'):
                if '|' in line:
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0][:8],
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3]
                        })
            
            return commits
            
        except Exception as e:
            print(colored(f"Error getting commits: {e}", "red"))
            return []
    
    async def _run_git_command(self, args: List[str]) -> Dict[str, Any]:
        """Run a git command and return result."""
        try:
            process = await asyncio.create_subprocess_exec(
                'git', *args,
                cwd=self.workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore')
            }
            
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }


class ToolAgentManager:
    """Manager for all tool agents."""
    
    def __init__(self):
        self.api_agent = APIToolAgent()
        self.code_agent = CodeAnalysisToolAgent()
        self.git_agent: Optional[GitToolAgent] = None
    
    def initialize_git_agent(self, workspace_dir: Path):
        """Initialize Git tool agent for a specific workspace."""
        self.git_agent = GitToolAgent(workspace_dir)
    
    async def analyze_file_change(self, file_path: str, old_content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a file change using the code analysis agent."""
        return await self.code_agent.analyze_file_changes(file_path, old_content)
    
    async def get_git_info(self) -> Dict[str, Any]:
        """Get Git repository information."""
        if not self.git_agent:
            return {'error': 'Git agent not initialized'}
        
        status = await self.git_agent.get_git_status()
        commits = await self.git_agent.get_recent_commits()
        
        return {
            'status': status,
            'recent_commits': commits
        }
    
    async def make_api_request(self, *args, **kwargs) -> Dict[str, Any]:
        """Make an API request using the API agent."""
        r = await self.api_agent.make_api_call(*args, **kwargs)
        return r