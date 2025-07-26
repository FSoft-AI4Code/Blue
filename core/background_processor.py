"""
Background Processor - Continuous analysis engine that works during idle periods
to provide deeper insights and prepare strategic recommendations.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from termcolor import colored

@dataclass
class BackgroundAnalysis:
    """Results from background analysis."""
    analysis_type: str
    findings: List[str]
    recommendations: List[str]
    confidence: float
    timestamp: datetime
    file_paths: List[str]

@dataclass
class TechnologyTrend:
    """Technology trend information."""
    technology: str
    description: str
    benefits: List[str]
    migration_effort: str  # "low", "medium", "high"
    relevance_score: float
    applicable_patterns: List[str]

class BackgroundProcessor:
    """
    Background processing engine that performs deep analysis during idle periods.
    
    Features:
    - Idle detection and automatic background analysis
    - Code pattern mining and anti-pattern detection
    - Technology trend analysis and recommendations
    - Architectural health assessment
    - Performance optimization opportunities
    """
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.is_running = False
        self.last_activity_time = datetime.now()
        self.idle_threshold = 30.0  # seconds of inactivity before starting background work
        
        # Analysis state
        self.background_task: Optional[asyncio.Task] = None
        self.analysis_results: List[BackgroundAnalysis] = []
        self.processed_files: Set[str] = set()
        
        # Technology trends database
        self.tech_trends = self._initialize_tech_trends()
        
        # Analysis intervals
        self.analysis_intervals = {
            'code_patterns': 60,      # Check for patterns every minute
            'tech_trends': 300,       # Check trends every 5 minutes
            'architecture': 600,      # Deep architecture analysis every 10 minutes
            'performance': 180        # Performance analysis every 3 minutes
        }
        
        self.last_analysis = {key: datetime.min for key in self.analysis_intervals}
    
    async def start(self):
        """Start the background processing engine."""
        if self.is_running:
            return
        
        self.is_running = True
        self.background_task = asyncio.create_task(self._background_loop())
        # Background processor started silently
    
    async def stop(self):
        """Stop the background processing engine."""
        self.is_running = False
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        # Background processor stopped silently
    
    def update_activity(self):
        """Signal that user activity has occurred."""
        self.last_activity_time = datetime.now()
    
    def is_idle(self) -> bool:
        """Check if system has been idle long enough for background processing."""
        return (datetime.now() - self.last_activity_time).total_seconds() > self.idle_threshold
    
    async def _background_loop(self):
        """Main background processing loop."""
        while self.is_running:
            try:
                # Only process during idle periods
                if self.is_idle():
                    await self._perform_background_analysis()
                
                # Check every 5 seconds
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(colored(f"Background processing error: {e}", "red"))
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _perform_background_analysis(self):
        """Perform various types of background analysis."""
        now = datetime.now()
        
        # Code pattern analysis
        if (now - self.last_analysis['code_patterns']).total_seconds() > self.analysis_intervals['code_patterns']:
            await self._analyze_code_patterns()
            self.last_analysis['code_patterns'] = now
        
        # Technology trend analysis
        if (now - self.last_analysis['tech_trends']).total_seconds() > self.analysis_intervals['tech_trends']:
            await self._analyze_technology_trends()
            self.last_analysis['tech_trends'] = now
        
        # Architecture health analysis
        if (now - self.last_analysis['architecture']).total_seconds() > self.analysis_intervals['architecture']:
            await self._analyze_architecture_health()
            self.last_analysis['architecture'] = now
        
        # Performance analysis
        if (now - self.last_analysis['performance']).total_seconds() > self.analysis_intervals['performance']:
            await self._analyze_performance_opportunities()
            self.last_analysis['performance'] = now
    
    async def _analyze_code_patterns(self):
        """Analyze code for patterns, anti-patterns, and improvement opportunities."""
        try:
            findings = []
            recommendations = []
            analyzed_files = []
            
            # Scan Python files for patterns
            for py_file in self.workspace_dir.rglob("*.py"):
                if self._should_analyze_file(py_file):
                    patterns = await self._analyze_file_patterns(py_file)
                    if patterns:
                        findings.extend(patterns)
                        analyzed_files.append(str(py_file))
            
            # Generate recommendations based on findings
            if findings:
                recommendations = self._generate_pattern_recommendations(findings)
                
                analysis = BackgroundAnalysis(
                    analysis_type="code_patterns",
                    findings=findings,
                    recommendations=recommendations,
                    confidence=0.8,
                    timestamp=datetime.now(),
                    file_paths=analyzed_files
                )
                
                self.analysis_results.append(analysis)
                
                # Limit results history
                if len(self.analysis_results) > 50:
                    self.analysis_results = self.analysis_results[-25:]
                
                # Naturally communicate insights like a human would
                await self._communicate_insights_naturally(findings, "code_patterns")
                
        except Exception as e:
            print(colored(f"Code pattern analysis error: {e}", "red"))
    
    async def _analyze_file_patterns(self, file_path: Path) -> List[str]:
        """Analyze a single file for patterns and anti-patterns."""
        patterns = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Function complexity analysis
            in_function = False
            function_lines = 0
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Detect function definitions
                if stripped.startswith('def ') or stripped.startswith('async def '):
                    if in_function and function_lines > 20:
                        patterns.append(f"Long function detected in {file_path.name} ({function_lines} lines)")
                    in_function = True
                    function_lines = 0
                    indent_level = len(line) - len(line.lstrip())
                
                if in_function:
                    function_lines += 1
                    
                    # Check for deeply nested code
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent > indent_level + 16:  # 4 levels of indentation
                        patterns.append(f"Deep nesting detected in {file_path.name}")
                    
                    # End of function
                    if stripped and current_indent <= indent_level and not stripped.startswith('def '):
                        if function_lines > 20:
                            patterns.append(f"Long function detected in {file_path.name} ({function_lines} lines)")
                        in_function = False
            
            # Check for code duplication patterns
            if content.count('def ') > 10:  # Many functions
                patterns.append(f"High function count in {file_path.name} - consider splitting")
            
            # Check for import patterns
            import_count = content.count('import ')
            if import_count > 15:
                patterns.append(f"Many imports in {file_path.name} ({import_count}) - review dependencies")
            
        except Exception as e:
            patterns.append(f"Analysis error in {file_path.name}: {str(e)[:50]}")
        
        return patterns
    
    async def _analyze_technology_trends(self):
        """Analyze codebase for opportunities to adopt newer technologies."""
        try:
            findings = []
            recommendations = []
            analyzed_files = []
            
            # Scan for technology opportunities
            for file_path in self.workspace_dir.rglob("*.py"):
                if self._should_analyze_file(file_path):
                    trends = await self._analyze_file_tech_trends(file_path)
                    if trends:
                        findings.extend(trends)
                        analyzed_files.append(str(file_path))
            
            # Check requirements.txt for outdated dependencies
            req_file = self.workspace_dir / "requirements.txt"
            if req_file.exists():
                dep_trends = await self._analyze_dependencies(req_file)
                findings.extend(dep_trends)
                analyzed_files.append(str(req_file))
            
            if findings:
                recommendations = self._generate_tech_recommendations(findings)
                
                analysis = BackgroundAnalysis(
                    analysis_type="technology_trends",
                    findings=findings,
                    recommendations=recommendations,
                    confidence=0.7,
                    timestamp=datetime.now(),
                    file_paths=analyzed_files
                )
                
                self.analysis_results.append(analysis)
                await self._communicate_insights_naturally(findings, "technology_trends")
                
        except Exception as e:
            print(colored(f"Technology trend analysis error: {e}", "red"))
    
    async def _analyze_file_tech_trends(self, file_path: Path) -> List[str]:
        """Analyze a file for technology trend opportunities."""
        trends = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for outdated patterns
            outdated_patterns = {
                'format(': 'Consider f-strings for string formatting (Python 3.6+)',
                '.format(': 'Consider f-strings for string formatting (Python 3.6+)',
                'os.path.join': 'Consider pathlib.Path for path operations (Python 3.4+)',
                'urllib2': 'Consider requests library for HTTP operations',
                'ConfigParser': 'Consider tomli/tomllib for TOML config files',
                'json.loads': 'Consider pydantic for data validation',
                'subprocess.call': 'Consider subprocess.run for better subprocess handling'
            }
            
            for pattern, suggestion in outdated_patterns.items():
                if pattern in content:
                    trends.append(f"{file_path.name}: {suggestion}")
            
            # Check for async opportunities
            if 'def ' in content and 'async def' not in content and ('requests.' in content or 'urllib' in content):
                trends.append(f"{file_path.name}: Consider async/await for HTTP operations")
            
            # Check for type hints
            if 'def ' in content and '-> ' not in content and 'from typing import' not in content:
                trends.append(f"{file_path.name}: Consider adding type hints for better code clarity")
                
        except Exception as e:
            trends.append(f"Tech trend analysis error in {file_path.name}: {str(e)[:50]}")
        
        return trends
    
    async def _analyze_dependencies(self, req_file: Path) -> List[str]:
        """Analyze requirements.txt for outdated dependencies."""
        trends = []
        
        try:
            with open(req_file, 'r') as f:
                content = f.read()
            
            # Check for potentially outdated packages
            outdated_suggestions = {
                'requests': 'Modern: httpx for async HTTP with better performance',
                'flask': 'Modern: FastAPI for API development with auto-docs',
                'argparse': 'Modern: typer or click for better CLI experience',
                'configparser': 'Modern: pydantic-settings for configuration',
                'unittest': 'Modern: pytest for more powerful testing'
            }
            
            for package, suggestion in outdated_suggestions.items():
                if package in content.lower():
                    trends.append(f"Dependency upgrade opportunity: {suggestion}")
                    
        except Exception as e:
            trends.append(f"Dependency analysis error: {str(e)[:50]}")
        
        return trends
    
    async def _analyze_architecture_health(self):
        """Perform deep architectural analysis."""
        try:
            findings = []
            
            # Count files by type
            file_counts = {}
            total_lines = 0
            
            for file_path in self.workspace_dir.rglob("*.py"):
                if self._should_analyze_file(file_path):
                    file_type = self._classify_file_type(file_path)
                    file_counts[file_type] = file_counts.get(file_type, 0) + 1
                    
                    try:
                        with open(file_path, 'r') as f:
                            total_lines += len(f.readlines())
                    except:
                        pass
            
            # Architectural health checks
            if file_counts.get('models', 0) == 0 and total_lines > 500:
                findings.append("Consider separating data models for better organization")
            
            if file_counts.get('utils', 0) > file_counts.get('core', 0) * 2:
                findings.append("High utility-to-core ratio suggests potential architectural debt")
            
            if total_lines > 5000 and file_counts.get('tests', 0) < file_counts.get('core', 0):
                findings.append("Test coverage may be insufficient for codebase size")
            
            if findings:
                analysis = BackgroundAnalysis(
                    analysis_type="architecture_health",
                    findings=findings,
                    recommendations=self._generate_architecture_recommendations(findings),
                    confidence=0.6,
                    timestamp=datetime.now(),
                    file_paths=[str(self.workspace_dir)]
                )
                
                self.analysis_results.append(analysis)
                await self._communicate_insights_naturally(findings, "architecture_health")
                
        except Exception as e:
            print(colored(f"Architecture analysis error: {e}", "red"))
    
    async def _analyze_performance_opportunities(self):
        """Analyze for performance optimization opportunities."""
        try:
            findings = []
            
            for file_path in self.workspace_dir.rglob("*.py"):
                if self._should_analyze_file(file_path):
                    perf_issues = await self._analyze_file_performance(file_path)
                    findings.extend(perf_issues)
            
            if findings:
                analysis = BackgroundAnalysis(
                    analysis_type="performance_opportunities",
                    findings=findings,
                    recommendations=self._generate_performance_recommendations(findings),
                    confidence=0.7,
                    timestamp=datetime.now(),
                    file_paths=[]
                )
                
                self.analysis_results.append(analysis)
                await self._communicate_insights_naturally(findings, "performance_opportunities")
                
        except Exception as e:
            print(colored(f"Performance analysis error: {e}", "red"))
    
    async def _analyze_file_performance(self, file_path: Path) -> List[str]:
        """Analyze a file for performance issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for potential performance issues
            if 'for ' in content and 'append(' in content:
                issues.append(f"{file_path.name}: Consider list comprehension instead of for-loop with append")
            
            if content.count('import ') > 20:
                issues.append(f"{file_path.name}: Many imports may slow startup time")
            
            if 'time.sleep(' in content:
                issues.append(f"{file_path.name}: Consider asyncio.sleep for non-blocking delays")
                
        except Exception:
            pass
        
        return issues
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        # Skip certain directories and files
        skip_patterns = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'env'}
        
        for part in file_path.parts:
            if part in skip_patterns:
                return False
        
        return True
    
    def _classify_file_type(self, file_path: Path) -> str:
        """Classify file type based on name and location."""
        name = file_path.name.lower()
        
        if 'test' in name:
            return 'tests'
        elif 'model' in name:
            return 'models'
        elif 'util' in name or 'helper' in name:
            return 'utils'
        elif 'main' in name or 'app' in name:
            return 'entry'
        else:
            return 'core'
    
    def _generate_pattern_recommendations(self, findings: List[str]) -> List[str]:
        """Generate recommendations based on code pattern findings."""
        recommendations = []
        
        for finding in findings:
            if 'Long function' in finding:
                recommendations.append("Break down long functions using Extract Method refactoring")
            elif 'Deep nesting' in finding:
                recommendations.append("Reduce nesting with guard clauses and early returns")
            elif 'High function count' in finding:
                recommendations.append("Consider splitting into multiple modules or classes")
            elif 'Many imports' in finding:
                recommendations.append("Review and consolidate imports, consider dependency injection")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_tech_recommendations(self, findings: List[str]) -> List[str]:
        """Generate technology trend recommendations."""
        recommendations = []
        
        for finding in findings:
            if 'f-strings' in finding:
                recommendations.append("Migrate to f-string formatting for better performance and readability")
            elif 'pathlib' in finding:
                recommendations.append("Adopt pathlib.Path for more robust path handling")
            elif 'async/await' in finding:
                recommendations.append("Consider async programming for I/O-bound operations")
            elif 'type hints' in finding:
                recommendations.append("Add type hints gradually, starting with public APIs")
        
        return list(set(recommendations))
    
    def _generate_architecture_recommendations(self, findings: List[str]) -> List[str]:
        """Generate architecture recommendations."""
        return [
            "Consider implementing proper separation of concerns",
            "Review module dependencies and reduce coupling",
            "Implement consistent error handling patterns"
        ]
    
    def _generate_performance_recommendations(self, findings: List[str]) -> List[str]:
        """Generate performance recommendations."""
        return [
            "Profile code to identify actual bottlenecks",
            "Consider caching for expensive operations",
            "Review algorithms for better time complexity"
        ]
    
    def _initialize_tech_trends(self) -> List[TechnologyTrend]:
        """Initialize the technology trends database."""
        return [
            TechnologyTrend(
                technology="asyncio",
                description="Asynchronous programming for I/O-bound operations",
                benefits=["Better performance", "Resource efficiency", "Scalability"],
                migration_effort="medium",
                relevance_score=0.9,
                applicable_patterns=["HTTP requests", "File I/O", "Database operations"]
            ),
            TechnologyTrend(
                technology="type_hints",
                description="Static type checking for Python",
                benefits=["Better IDE support", "Fewer bugs", "Self-documenting code"],
                migration_effort="low",
                relevance_score=0.8,
                applicable_patterns=["Function definitions", "Class attributes", "API interfaces"]
            ),
            TechnologyTrend(
                technology="pathlib",
                description="Object-oriented path handling",
                benefits=["Cross-platform compatibility", "Cleaner code", "Better error handling"],
                migration_effort="low",
                relevance_score=0.7,
                applicable_patterns=["File operations", "Path manipulation", "Directory traversal"]
            )
        ]
    
    def get_recent_analyses(self, limit: int = 5) -> List[BackgroundAnalysis]:
        """Get recent background analysis results."""
        return sorted(self.analysis_results, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all background analyses."""
        if not self.analysis_results:
            return {"total_analyses": 0, "findings": 0, "recommendations": 0}
        
        total_findings = sum(len(analysis.findings) for analysis in self.analysis_results)
        total_recommendations = sum(len(analysis.recommendations) for analysis in self.analysis_results)
        
        return {
            "total_analyses": len(self.analysis_results),
            "findings": total_findings,
            "recommendations": total_recommendations,
            "last_analysis": self.analysis_results[-1].timestamp if self.analysis_results else None,
            "idle_threshold": self.idle_threshold
        }
    
    async def _communicate_insights_naturally(self, findings: List[str], analysis_type: str):
        """Use AI to naturally communicate insights like a real human pair programmer."""
        if not findings or len(findings) == 0:
            return
        
        try:
            # Get recent file changes context
            recent_files = self._get_recent_file_context()
            
            # Create a system prompt for the AI to act as a human pair programmer
            system_prompt = f"""You are a thoughtful pair programming partner sitting next to your colleague. You've been quietly observing their code and just noticed some things during your {analysis_type} review.

WHAT YOU OBSERVED:
{chr(10).join(findings)}

RECENT FILE CONTEXT:
{recent_files}

As a helpful colleague, decide if any of these observations are worth mentioning casually. If so, make ONE brief, natural comment (1-2 sentences max) like you would to a friend. 

Rules:
- Only comment if it's genuinely helpful/interesting
- Sound casual and human, not robotic
- Use "I noticed..." / "Just saw..." / "By the way..." 
- No formal analysis reports
- If nothing is worth mentioning, respond with "SKIP"

Example good responses:
- "I noticed a few functions getting pretty long - might be worth splitting them up when you get a chance"
- "Just saw some old string formatting in there - f-strings would be cleaner"
- "By the way, seeing quite a bit of nesting building up"

Respond with either your casual comment or "SKIP"."""

            # Use AI to generate natural communication
            ai_response = await self._make_ai_request(system_prompt, max_tokens=100)
            
            if ai_response and ai_response.strip() != "SKIP" and len(ai_response.strip()) > 5:
                # AI decided to communicate something naturally
                print(colored(f"💭 {ai_response.strip()}", "blue"))
                
        except Exception as e:
            # Fail silently - background insights are not critical
            pass
    
    def _get_recent_file_context(self) -> str:
        """Get context about recent file changes."""
        # This would ideally come from the file change events
        # For now, return basic context
        return "User has been actively editing Python files in the project"
    
    async def _make_ai_request(self, prompt: str, max_tokens: int = 150) -> str:
        """Make AI request for natural communication."""
        try:
            # Import here to avoid circular dependencies
            from utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # Use the same AI provider as the navigator
            ai_provider = config_manager.get('preferences.ai_provider', 'openai')
            
            if ai_provider == 'anthropic':
                api_key = config_manager.get_api_key('anthropic')
                if api_key:
                    import anthropic
                    client = anthropic.AsyncAnthropic(api_key=api_key)
                    response = await client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
            else:
                api_key = config_manager.get_api_key('openai')
                if api_key:
                    from openai import AsyncOpenAI
                    client = AsyncOpenAI(api_key=api_key)
                    response = await client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.choices[0].message.content
            
            return "SKIP"
            
        except Exception as e:
            return "SKIP"