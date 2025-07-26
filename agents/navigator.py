"""
Navigator Agent - Central LLM-powered core for goal management, graph operations,
big-picture synthesis, and dynamic decision algorithm for interventions.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from termcolor import colored

# import autogen  # Temporarily disabled due to version conflicts
from openai import AsyncOpenAI
import anthropic

from core.workspace_graph import WorkspaceGraph
from core.decision_algorithm import DecisionAlgorithm


class NavigatorAgent:
    """
    Navigator Agent handles:
    - Goal management and decomposition
    - Workspace graph operations and traversal
    - Big-picture synthesis and strategic insights
    - Dynamic decision making for interventions
    - Feedback learning and parameter adjustment
    """
    
    def __init__(self, workspace_graph: WorkspaceGraph, decision_algorithm: DecisionAlgorithm, config_manager=None):
        self.workspace_graph = workspace_graph
        self.decision_algorithm = decision_algorithm
        self.config_manager = config_manager
        
        # Determine AI provider and initialize client
        self.ai_provider = self._get_ai_provider()
        self.client = self._init_ai_client()
        
        # Navigator state
        self.current_goal: Optional[str] = None
        self.goal_subtasks: List[str] = []
        self.conversation_history: List[Dict[str, str]] = []
        self.feedback_history: List[Dict[str, Any]] = []
        
        # Model configuration based on provider
        self.model_config = self._get_model_config()
        
        # AutoGen configuration
        self.config_list = [self.model_config]
        
        # Initialize AutoGen assistant
        self._init_autogen_assistant()
    
    def _get_ai_provider(self) -> str:
        """Get the configured AI provider."""
        if self.config_manager:
            return self.config_manager.get('preferences.ai_provider', 'anthropic')
        
        # Fallback: check environment variables (prefer Anthropic)
        import os
        if os.environ.get('ANTHROPIC_API_KEY'):
            return 'anthropic'
        elif os.environ.get('OPENAI_API_KEY'):
            return 'openai'
        return 'anthropic'  # Default to Anthropic
    
    def _init_ai_client(self):
        """Initialize the appropriate AI client based on provider."""
        if self.ai_provider == 'anthropic':
            return anthropic.AsyncAnthropic()  # Will use ANTHROPIC_API_KEY from environment
        else:
            return AsyncOpenAI()  # Will use OPENAI_API_KEY from environment
    
    def _get_model_config(self) -> Dict[str, Any]:
        """Get model configuration based on AI provider."""
        if self.ai_provider == 'anthropic':
            return {
                "model": "claude-3-5-sonnet-20241022",  # Use Claude 3.5 Sonnet for strategic thinking
                "api_key": None,  # Will be loaded from environment
                "api_type": "anthropic"
            }
        else:
            return {
                "model": "gpt-4",  # Use GPT-4 for strategic thinking
                "api_key": None,  # Will be loaded from environment
                "api_type": "openai"
            }
    
    async def _make_ai_request(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 300) -> Optional[str]:
        """Make a request to the configured AI provider."""
        try:
            if self.ai_provider == 'anthropic':
                # Anthropic requires system message as separate parameter
                system_message = None
                user_messages = []
                
                for msg in messages:
                    if msg['role'] == 'system':
                        system_message = msg['content']
                    else:
                        user_messages.append(msg)
                
                # Build request parameters
                request_params = {
                    'model': self.model_config["model"],
                    'messages': user_messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                
                # Add system message if present
                if system_message:
                    request_params['system'] = system_message
                
                response = await self.client.messages.create(**request_params)
                return response.content[0].text
            else:
                response = await self.client.chat.completions.create(
                    model=self.model_config["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            print(colored(f"Error making AI request ({self.ai_provider}): {e}", "red"))
            return None
    
    def _init_autogen_assistant(self):
        """Initialize AutoGen assistant for transparent agent conversations."""
        # Temporarily disabled due to version conflicts
        self.assistant = None  # Placeholder until autogen is fixed
        
        # Original autogen code (commented out):
        # self.assistant = autogen.AssistantAgent(
        #     name="navigator",
        #     system_message="""You are the Navigator Agent for Blue CLI, a strategic pair programming assistant.
        #     
        #     Your role is to:
        #     1. Provide big-picture strategic guidance aligned with the user's goals
        #     2. Identify potential blind spots and architectural concerns
        #     3. Suggest high-level approaches without micromanaging implementation details
        #     4. Maintain empathy and collaborative tone
        #     5. Focus on scalability, maintainability, and goal coherence
        #     
        #     Always respond with strategic insights like:
        #     - "On your [goal]: Observing the emerging structure—graph flags [concern] risking [impact] per [source]. Big pic: [suggestion]? Preview idea: [specific approach]. Your thoughts?"
        #     
        #     Keep responses concise, strategic, and thought-provoking.
        #     Avoid low-level implementation details unless specifically asked.
        #     """,
        #     llm_config={"config_list": self.config_list}
        # )
    
    async def set_goal(self, goal: str):
        """Set the current programming goal and decompose it."""
        self.current_goal = goal
        
        # Decompose goal into subtasks
        self.goal_subtasks = await self.decompose_goal(goal)
        
        # Add goal to workspace graph
        await self.workspace_graph.add_goal_node(goal, self.goal_subtasks)
        
        # Reset decision algorithm for new goal
        self.decision_algorithm.reset_for_new_goal()
    
    async def decompose_goal(self, goal: str) -> List[str]:
        """Decompose a high-level goal into actionable subtasks with enhanced analysis."""
        try:
            # Analyze current workspace context for smarter decomposition
            graph_context = await self._build_graph_context()
            existing_files = await self._analyze_existing_codebase()
            
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert software architect helping decompose goals into strategic subtasks.
                    
                    Current Workspace Context:
                    {graph_context}
                    
                    Existing Codebase Analysis:
                    {existing_files}
                    
                    Decompose the goal considering:
                    1. Existing code structure and patterns
                    2. Potential integration points
                    3. Risk mitigation strategies
                    4. Performance and scalability implications
                    5. Testing and validation requirements
                    
                    Return a JSON list of 4-8 strategic subtasks with priorities:
                    {{
                        "subtasks": [
                            {{"task": "Analyze existing authentication patterns", "priority": "high", "reasoning": "Foundation for design decisions"}},
                            {{"task": "Design secure token management system", "priority": "high", "reasoning": "Core security requirement"}}
                        ]
                    }}
                    
                    Focus on strategic planning, not implementation details.
                    """
                },
                {
                    "role": "user",
                    "content": f"Goal: {goal}"
                }
            ]
            
            subtasks_text = await self._make_ai_request(messages, temperature=0.2, max_tokens=800)
            
            if not subtasks_text:
                return []
            
            # Try to parse enhanced JSON format
            try:
                result = json.loads(subtasks_text)
                if isinstance(result, dict) and 'subtasks' in result:
                    return [item['task'] for item in result['subtasks']]
                elif isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
            
            # Fallback: parse as numbered list
            lines = subtasks_text.split('\n')
            subtasks = []
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    subtasks.append(re.sub(r'^\d+\.\s*', '', line))
                elif line and not line.startswith('#') and not line.startswith('{'):
                    subtasks.append(line)
            
            return subtasks[:8]  # Allow up to 8 subtasks
            
        except Exception as e:
            print(colored(f"Error decomposing goal: {e}", "red"))
            return []
    
    async def process_query(self, query: str, current_goal: Optional[str] = None) -> Optional[str]:
        """Process a user query and provide enhanced strategic guidance."""
        try:
            # Build comprehensive context
            graph_context = await self._build_graph_context()
            conversation_patterns = self._analyze_conversation_patterns()
            code_analysis = await self._analyze_code_patterns(query)
            
            # Determine query type for specialized handling
            query_type = self._classify_query(query)
            
            # Create enhanced system message with current context
            system_message = f"""You are an expert Navigator Agent providing strategic pair programming guidance.
            
            Current Goal: {current_goal or 'None set'}
            Subtasks: {', '.join(self.goal_subtasks) if self.goal_subtasks else 'None'}
            
            Workspace Context:
            {graph_context}
            
            Conversation Patterns:
            {conversation_patterns}
            
            Code Analysis:
            {code_analysis}
            
            Query Type: {query_type}
            
            Provide strategic, contextual guidance based on:
            - Current progress toward goal
            - Code quality and architectural patterns
            - Potential risks and optimization opportunities
            - Best practices and industry standards
            - Long-term maintainability implications
            
            Tailor your response to the query type:
            - Architecture: Focus on system design and patterns
            - Implementation: Suggest approaches and best practices  
            - Debugging: Guide toward root cause analysis
            - Planning: Help break down and prioritize work
            - Review: Provide constructive feedback and improvements
            
            Format responses as strategic insights with actionable recommendations.
            - Architecture alignment
            - Scalability implications  
            - Maintainability concerns
            - Goal coherence
            - Potential blind spots
            
            Keep responses insightful, actionable, and aligned with the user's current context.
            """
            
            # Include relevant conversation history for better context
            messages = [{"role": "system", "content": system_message}]
            
            # Add recent relevant conversations
            recent_history = self._get_relevant_history(query, limit=3)
            for hist in recent_history:
                messages.append({"role": "user", "content": hist['query']})
                messages.append({"role": "assistant", "content": hist['response']})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Adjust parameters based on query type
            temperature = 0.8 if query_type in ['architecture', 'planning'] else 0.6
            max_tokens = 600 if query_type in ['review', 'debugging'] else 400
            
            assistant_response = await self._make_ai_request(messages, temperature=temperature, max_tokens=max_tokens)
            
            if not assistant_response:
                return None
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": assistant_response,
                "goal": current_goal
            })
            
            return assistant_response
            
        except Exception as e:
            print(colored(f"Error processing query: {e}", "red"))
            return None
    
    async def generate_strategic_suggestion(self, event_context: Dict[str, Any], goal: Optional[str]) -> Optional[str]:
        """Generate enhanced strategic suggestions based on comprehensive analysis."""
        try:
            # Build comprehensive context
            graph_context = await self._build_graph_context()
            code_analysis = await self._analyze_existing_codebase()
            conversation_patterns = self._analyze_conversation_patterns()
            
            # Analyze event significance
            event_significance = self._analyze_event_significance(event_context)
            
            # Get goal progress if available
            goal_progress = await self._assess_goal_progress(goal)
            
            system_message = f"""You are an expert Navigator Agent providing strategic interventions based on comprehensive workspace analysis.
            
            Current Goal: {goal or 'None set'}
            Goal Progress: {goal_progress}
            Subtasks: {', '.join(self.goal_subtasks) if self.goal_subtasks else 'None defined'}
            
            Recent Event Analysis:
            {json.dumps(event_context, indent=2)}
            Event Significance: {event_significance}
            
            Workspace Context:
            {graph_context}
            
            Codebase Analysis:
            {code_analysis}
            
            Conversation Patterns:
            {conversation_patterns}
            
            Generate strategic suggestions that:
            1. Are contextually relevant to current progress and events
            2. Identify potential architectural risks or opportunities
            3. Suggest proactive improvements or course corrections
            4. Consider long-term maintainability and scalability
            5. Align with established development patterns
            
            Only suggest if there's genuine strategic value. Consider:
            - Are we deviating from the goal?
            - Are there emerging patterns that need attention?
            - Could we prevent future technical debt?
            - Are there optimization opportunities?
            
            Format options:
            - Architecture: "Goal progress: [status]. Observing [pattern] suggests [risk/opportunity]. Consider [strategic approach]?"
            - Quality: "Code pattern emerging: [observation]. This might [impact]. Strategic pivot: [suggestion]?"
            - Process: "Development flow shows [trend]. To maintain [goal aspect], consider [approach]?"
            
            Return "NO_SUGGESTION" if no strategic value warrants intervention.
            Keep responses concise but insightful (2-3 sentences max).
            """
            
            messages = [{"role": "system", "content": system_message}]
            
            suggestion = await self._make_ai_request(messages, temperature=0.5, max_tokens=200)
            
            if not suggestion or "NO_SUGGESTION" in suggestion:
                return None
            
            return suggestion.strip()
            
        except Exception as e:
            print(colored(f"Error generating suggestion: {e}", "red"))
            return None
    
    async def explain_suggestion(self, suggestion: str) -> str:
        """Provide detailed explanation for a suggestion."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Provide a detailed explanation of the strategic reasoning behind this suggestion. Focus on potential risks, architectural concerns, and long-term implications."
                },
                {
                    "role": "user",
                    "content": f"Explain this suggestion: {suggestion}"
                }
            ]
            
            explanation = await self._make_ai_request(messages, temperature=0.5, max_tokens=250)
            
            return explanation or f"Unable to explain suggestion."
            
        except Exception as e:
            return f"Unable to explain suggestion: {e}"
    
    async def generate_strategic_suggestion(self, event_data: Dict[str, Any], 
                                          current_goal: Optional[str], 
                                          decision_details: Dict[str, Any]) -> Optional[str]:
        """Generate strategic suggestions based on file changes and decision context."""
        try:
            # Extract decision context
            confidence = decision_details.get('confidence', 0)
            reasoning = decision_details.get('reasoning', '')
            total_score = decision_details.get('total_score', 0)
            threshold = decision_details.get('threshold', 0)
            
            # Determine the type of strategic intervention needed
            intervention_type = self._classify_intervention_type(event_data, decision_details, reasoning)
            
            # Generate context-aware suggestion
            suggestion = await self._generate_contextual_suggestion(
                intervention_type, event_data, current_goal, decision_details
            )
            
            return suggestion
            
        except Exception as e:
            print(colored(f"Error generating suggestion: {e}", "red"))
            return None
    
    def _classify_intervention_type(self, event_data: Dict[str, Any], 
                                  decision_details: Dict[str, Any], 
                                  reasoning: str) -> str:
        """Classify the type of intervention needed based on context."""
        
        # Check for specific patterns in reasoning
        if "architectural changes" in reasoning.lower():
            return "architectural_review"
        elif "goal drift" in reasoning.lower() or "goal" in reasoning.lower():
            return "goal_alignment"
        elif "high development pace" in reasoning.lower() or "momentum" in reasoning.lower():
            return "pace_checkpoint"
        elif "complexity" in reasoning.lower():
            return "complexity_concern"
        elif "strategic moment" in reasoning.lower():
            return "strategic_pause"
        else:
            return "general_checkpoint"
    
    async def _generate_contextual_suggestion(self, intervention_type: str,
                                            event_data: Dict[str, Any],
                                            current_goal: Optional[str],
                                            decision_details: Dict[str, Any]) -> str:
        """Generate AI-driven contextual suggestions based on actual code analysis."""
        
        try:
            # Get file information
            file_path = event_data.get('src_path')
            if not file_path:
                return "Strategic checkpoint triggered - no specific file context available."
            
            # Read current file content
            file_content = await self._read_file_safely(file_path)
            if not file_content:
                return f"Detected changes in {Path(file_path).name} - unable to analyze content."
            
            # Get accumulated context from recent changes
            recent_context = await self._get_accumulated_context()
            
            # Generate AI-driven strategic suggestion
            suggestion = await self._generate_ai_suggestion(
                file_path=file_path,
                file_content=file_content,
                intervention_type=intervention_type,
                current_goal=current_goal,
                recent_context=recent_context,
                decision_details=decision_details
            )
            
            return suggestion or "Strategic moment detected - worth pausing to assess current direction."
            
        except Exception as e:
            print(colored(f"Error generating contextual suggestion: {e}", "red"))
            # Fallback to simple suggestion
            file_name = Path(file_path).name if file_path else "files"
            return f"On your {current_goal or 'current work'}: Changes detected in {file_name}. Strategic checkpoint - how are we tracking?"
    
    async def _read_file_safely(self, file_path: str) -> Optional[str]:
        """Safely read file content for analysis."""
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return None
            
            # Limit file size to avoid huge files
            if path.stat().st_size > 50000:  # 50KB limit
                return f"[File too large for analysis: {path.stat().st_size} bytes]"
            
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(colored(f"Error reading file {file_path}: {e}", "red"))
            return None
    
    async def _get_accumulated_context(self) -> str:
        """Get accumulated context from recent changes and goals."""
        context_parts = []
        
        # Add current goal context
        if self.current_goal:
            context_parts.append(f"Current goal: {self.current_goal}")
        
        # Add subtasks if available
        if self.goal_subtasks:
            context_parts.append(f"Subtasks: {', '.join(self.goal_subtasks[:3])}")
        
        # Add recent query context
        if self.query_history:
            recent_queries = list(self.query_history)[-3:]
            context_parts.append(f"Recent context: {', '.join(recent_queries)}")
        
        # Add feedback context
        if self.feedback_history:
            recent_feedback = self.feedback_history[-5:]
            positive_count = sum(1 for f in recent_feedback if f['positive'])
            context_parts.append(f"Recent feedback: {positive_count}/{len(recent_feedback)} positive")
        
        return " | ".join(context_parts) if context_parts else "No accumulated context available"
    
    async def _generate_ai_suggestion(self, file_path: str, file_content: str, 
                                    intervention_type: str, current_goal: Optional[str],
                                    recent_context: str, decision_details: Dict[str, Any]) -> Optional[str]:
        """Generate AI-driven strategic suggestion based on actual code analysis."""
        
        try:
            file_name = Path(file_path).name
            
            # Create analysis prompt for AI
            prompt = f"""You are an expert pair programming navigator providing strategic insights. 

CONTEXT:
- File: {file_name}
- Goal: {current_goal or 'No specific goal set'}
- Intervention type: {intervention_type}
- Confidence: {decision_details.get('confidence', 0):.0f}%
- Recent context: {recent_context}

FILE CONTENT (last 50 lines):
{self._truncate_content(file_content)}

As a strategic pair programming partner, analyze this code and provide a concise, actionable insight. Focus on:
1. What you observe happening in the code
2. Strategic implications for the goal
3. A specific suggestion or question

Format: "On your [goal]: [observation]. Big pic: [strategic insight]? Preview idea: [specific suggestion]."

Keep it conversational, insightful, and under 150 words."""

            # Use the configured AI provider
            response = await self._make_ai_request(prompt)
            
            if response and len(response.strip()) > 20:
                return response.strip()
            else:
                return None
                
        except Exception as e:
            print(colored(f"Error generating AI suggestion: {e}", "red"))
            return None
    
    def _truncate_content(self, content: str, max_lines: int = 50) -> str:
        """Truncate content to last N lines for analysis."""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
        # Take last 50 lines for most recent context
        truncated_lines = lines[-max_lines:]
        return f"[... showing last {max_lines} lines ...]\n" + '\n'.join(truncated_lines)

    async def record_feedback(self, positive: bool):
        """Record user feedback with enhanced learning and parameter adjustment."""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "positive": positive,
            "goal": self.current_goal,
            "recent_context": self.conversation_history[-3:] if self.conversation_history else [],
            "ai_provider": self.ai_provider,
            "response_length": len(self.conversation_history[-1].get('response', '')) if self.conversation_history else 0,
            "query_type": self._classify_query(self.conversation_history[-1].get('query', '')) if self.conversation_history else 'unknown'
        }
        
        self.feedback_history.append(feedback_entry)
        
        # Enhanced adaptive learning
        await self._adaptive_learning_update(positive, feedback_entry)
        
        # Adjust decision algorithm parameters based on feedback
        await self.decision_algorithm.adjust_from_feedback(positive)
        
        # Limit feedback history size
        if len(self.feedback_history) > 100:
            self.feedback_history = self.feedback_history[-50:]
    
    async def _build_graph_context(self) -> str:
        """Build enhanced context string from workspace graph for LLM consumption."""
        try:
            graph_summary = await self.workspace_graph.get_summary()
            
            context_parts = []
            
            # Add node counts with analysis
            if graph_summary.get('node_counts'):
                counts = graph_summary['node_counts']
                total_nodes = sum(counts.values())
                context_parts.append(f"Workspace scale: {total_nodes} nodes ({counts})")
                
                # Analyze graph complexity
                if total_nodes > 50:
                    context_parts.append("Scale: Large project - consider modularity")
                elif total_nodes > 20:
                    context_parts.append("Scale: Medium project - monitor dependencies")
                else:
                    context_parts.append("Scale: Small project - focus on structure")
            
            # Add recent changes with patterns
            if graph_summary.get('recent_changes'):
                changes = graph_summary['recent_changes'][:5]
                change_types = {}
                for change in changes:
                    change_type = change.get('type', 'unknown')
                    change_types[change_type] = change_types.get(change_type, 0) + 1
                
                context_parts.append(f"Recent activity: {dict(list(change_types.items())[:3])} patterns")
                
                # Analyze change velocity
                if len(changes) > 10:
                    context_parts.append("Velocity: High - ensure stability")
                elif len(changes) > 5:
                    context_parts.append("Velocity: Moderate - good progress")
                else:
                    context_parts.append("Velocity: Low - may need acceleration")
            
            # Add external links with categorization
            if graph_summary.get('external_links'):
                links = graph_summary['external_links'][:3]
                link_types = {}
                for link in links:
                    if 'api' in str(link).lower():
                        link_types['API'] = link_types.get('API', 0) + 1
                    elif 'doc' in str(link).lower():
                        link_types['Documentation'] = link_types.get('Documentation', 0) + 1
                    else:
                        link_types['External'] = link_types.get('External', 0) + 1
                
                context_parts.append(f"External dependencies: {link_types}")
            
            # Add potential concerns with severity
            if graph_summary.get('concerns'):
                concerns = graph_summary['concerns'][:3]
                context_parts.append(f"Strategic concerns: {len(concerns)} identified - {concerns[0] if concerns else 'none'}")
            
            # Add workspace health assessment
            health_score = self._calculate_workspace_health(graph_summary)
            context_parts.append(f"Workspace health: {health_score}")
            
            return '\n'.join(context_parts) if context_parts else "New workspace - establishing context"
            
        except Exception as e:
            return f"Context analysis limited: {str(e)[:50]}"
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get recent conversation history."""
        return self.conversation_history[-10:]  # Return last 10 conversations
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics for monitoring."""
        if not self.feedback_history:
            return {"total": 0, "positive_rate": 0}
        
        positive_count = sum(1 for fb in self.feedback_history if fb['positive'])
        total_count = len(self.feedback_history)
        
        return {
            "total": total_count,
            "positive_rate": positive_count / total_count if total_count > 0 else 0,
            "recent_feedback": self.feedback_history[-5:]
        }
    
    def switch_ai_provider(self, provider: str) -> bool:
        """
        Programmatically switch AI provider.
        
        Args:
            provider: 'openai' or 'anthropic'
            
        Returns:
            True if switch successful, False otherwise
        """
        if provider not in ['openai', 'anthropic']:
            print(colored(f"Invalid provider: {provider}. Use 'openai' or 'anthropic'", "red"))
            return False
        
        try:
            # Update config if available
            if self.config_manager:
                self.config_manager.set('preferences.ai_provider', provider)
            
            # Reinitialize with new provider
            self.ai_provider = provider
            self.client = self._init_ai_client()
            self.model_config = self._get_model_config()
            
            print(colored(f"Switched to {provider.title()} AI provider", "green"))
            return True
            
        except Exception as e:
            print(colored(f"Error switching to {provider}: {e}", "red"))
            return False
    
    def get_current_provider(self) -> str:
        """Get the currently active AI provider."""
        return self.ai_provider
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return ['openai', 'anthropic']
    
    async def _analyze_existing_codebase(self) -> str:
        """Analyze existing codebase structure for context."""
        try:
            # Get workspace summary from graph
            summary = await self.workspace_graph.get_summary()
            
            analysis_parts = []
            
            if summary.get('node_counts'):
                counts = summary['node_counts']
                analysis_parts.append(f"Files: {counts.get('file', 0)}, Dependencies: {counts.get('dependency', 0)}")
            
            # Analyze recent file patterns if available
            if summary.get('recent_changes'):
                changes = summary['recent_changes'][:5]
                file_types = {}
                for change in changes:
                    if 'file_path' in change:
                        ext = change['file_path'].split('.')[-1] if '.' in change['file_path'] else 'unknown'
                        file_types[ext] = file_types.get(ext, 0) + 1
                
                if file_types:
                    analysis_parts.append(f"Recent activity: {dict(list(file_types.items())[:3])}")
            
            return ' | '.join(analysis_parts) if analysis_parts else "New workspace"
            
        except Exception as e:
            return f"Analysis unavailable: {str(e)[:50]}"
    
    def _analyze_conversation_patterns(self) -> str:
        """Analyze conversation history for patterns and insights."""
        if not self.conversation_history:
            return "No conversation history"
        
        recent_convos = self.conversation_history[-5:]
        
        # Analyze query types
        query_types = []
        for convo in recent_convos:
            query = convo.get('query', '').lower()
            if any(word in query for word in ['how', 'implement', 'create', 'build']):
                query_types.append('implementation')
            elif any(word in query for word in ['why', 'architecture', 'design', 'pattern']):
                query_types.append('architecture')
            elif any(word in query for word in ['error', 'bug', 'issue', 'problem']):
                query_types.append('debugging')
            else:
                query_types.append('general')
        
        # Analyze response satisfaction (if feedback available)
        feedback_trend = "neutral"
        if len(self.feedback_history) >= 3:
            recent_feedback = self.feedback_history[-3:]
            positive_rate = sum(1 for fb in recent_feedback if fb.get('positive', False)) / len(recent_feedback)
            feedback_trend = "positive" if positive_rate > 0.6 else "needs improvement" if positive_rate < 0.4 else "mixed"
        
        return f"Recent focus: {', '.join(set(query_types[-3:]))} | Feedback trend: {feedback_trend}"
    
    async def _analyze_code_patterns(self, query: str) -> str:
        """Analyze code patterns relevant to the current query."""
        try:
            # Extract code-related keywords from query
            code_keywords = []
            query_lower = query.lower()
            
            # Language detection
            languages = ['python', 'javascript', 'typescript', 'java', 'cpp', 'go', 'rust']
            for lang in languages:
                if lang in query_lower:
                    code_keywords.append(f"lang:{lang}")
            
            # Pattern detection
            patterns = {
                'api': ['api', 'endpoint', 'route', 'rest'],
                'database': ['database', 'db', 'sql', 'query', 'schema'],
                'auth': ['auth', 'login', 'permission', 'token', 'session'],
                'frontend': ['ui', 'frontend', 'component', 'react', 'vue'],
                'backend': ['server', 'backend', 'service', 'microservice'],
                'testing': ['test', 'testing', 'unit test', 'integration']
            }
            
            for pattern, keywords in patterns.items():
                if any(kw in query_lower for kw in keywords):
                    code_keywords.append(f"pattern:{pattern}")
            
            return ' | '.join(code_keywords) if code_keywords else "General development"
            
        except Exception:
            return "Pattern analysis unavailable"
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query for specialized handling."""
        query_lower = query.lower()
        
        # Architecture and design queries
        if any(word in query_lower for word in ['architecture', 'design', 'pattern', 'structure', 'organize']):
            return 'architecture'
        
        # Implementation queries
        elif any(word in query_lower for word in ['how to', 'implement', 'create', 'build', 'develop']):
            return 'implementation'
        
        # Debugging queries
        elif any(word in query_lower for word in ['error', 'bug', 'issue', 'problem', 'debug', 'fix']):
            return 'debugging'
        
        # Planning queries
        elif any(word in query_lower for word in ['plan', 'strategy', 'approach', 'next steps', 'roadmap']):
            return 'planning'
        
        # Review queries
        elif any(word in query_lower for word in ['review', 'feedback', 'improve', 'optimize', 'refactor']):
            return 'review'
        
        return 'general'
    
    def _get_relevant_history(self, query: str, limit: int = 3) -> List[Dict[str, str]]:
        """Get conversation history relevant to the current query."""
        if not self.conversation_history:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score conversations by relevance
        scored_history = []
        for convo in self.conversation_history[-10:]:  # Only consider recent history
            response_words = set(convo.get('response', '').lower().split())
            query_words_hist = set(convo.get('query', '').lower().split())
            
            # Calculate relevance score
            relevance_score = len(query_words.intersection(response_words)) + \
                            len(query_words.intersection(query_words_hist)) * 2
            
            if relevance_score > 0:
                scored_history.append((relevance_score, convo))
        
        # Sort by relevance and return top results
        scored_history.sort(key=lambda x: x[0], reverse=True)
        return [convo for _, convo in scored_history[:limit]]
    
    def _analyze_event_significance(self, event_context: Dict[str, Any]) -> str:
        """Analyze the significance of recent events for strategic planning."""
        try:
            if not event_context:
                return "No recent events"
            
            significance_factors = []
            
            # Check event types
            if 'batch_info' in event_context:
                batch = event_context['batch_info']
                event_count = batch.get('event_count', 0)
                affected_files = batch.get('affected_files', [])
                event_types = batch.get('event_types', {})
                
                if event_count > 5:
                    significance_factors.append("high activity")
                
                if len(affected_files) > 3:
                    significance_factors.append("multiple files")
                
                if event_types.get('created', 0) > 0:
                    significance_factors.append("new files")
                
                if event_types.get('deleted', 0) > 0:
                    significance_factors.append("removed files")
            
            # Analyze file patterns
            if 'raw_events' in event_context:
                events = event_context['raw_events']
                file_extensions = {}
                for event in events:
                    src_path = event.get('src_path', '')
                    if '.' in src_path:
                        ext = src_path.split('.')[-1]
                        file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
                if len(file_extensions) > 1:
                    significance_factors.append(f"mixed types: {list(file_extensions.keys())[:3]}")
            
            return " | ".join(significance_factors) if significance_factors else "routine changes"
            
        except Exception:
            return "significance analysis unavailable"
    
    async def _assess_goal_progress(self, goal: Optional[str]) -> str:
        """Assess progress toward the current goal."""
        try:
            if not goal or not self.goal_subtasks:
                return "No goal set"
            
            # Simple heuristic based on conversation and feedback
            if not self.conversation_history:
                return "Just started"
            
            # Analyze recent conversation topics
            recent_queries = [convo.get('query', '').lower() for convo in self.conversation_history[-5:]]
            goal_words = set(goal.lower().split())
            
            # Calculate relevance to goal
            relevance_score = 0
            for query in recent_queries:
                query_words = set(query.split())
                relevance_score += len(goal_words.intersection(query_words))
            
            progress_indicators = []
            
            # Check conversation focus
            if relevance_score > 3:
                progress_indicators.append("on track")
            elif relevance_score > 0:
                progress_indicators.append("related work")
            else:
                progress_indicators.append("may be drifting")
            
            # Check subtask engagement
            subtask_mentions = 0
            for subtask in self.goal_subtasks:
                subtask_words = set(subtask.lower().split())
                for query in recent_queries:
                    if len(subtask_words.intersection(set(query.split()))) > 1:
                        subtask_mentions += 1
                        break
            
            if subtask_mentions > 0:
                progress_indicators.append(f"{subtask_mentions}/{len(self.goal_subtasks)} subtasks engaged")
            
            # Check feedback trend
            if len(self.feedback_history) >= 2:
                recent_feedback = self.feedback_history[-2:]
                positive_rate = sum(1 for fb in recent_feedback if fb.get('positive', False)) / len(recent_feedback)
                if positive_rate > 0.5:
                    progress_indicators.append("positive feedback")
                else:
                    progress_indicators.append("needs adjustment")
            
            return " | ".join(progress_indicators)
            
        except Exception:
            return "progress assessment unavailable"
    
    def _calculate_workspace_health(self, graph_summary: Dict[str, Any]) -> str:
        """Calculate overall workspace health score based on various metrics."""
        try:
            health_factors = []
            score = 0
            max_score = 0
            
            # Factor 1: Graph structure health
            if graph_summary.get('node_counts'):
                counts = graph_summary['node_counts']
                total_nodes = sum(counts.values())
                
                if total_nodes > 0:
                    max_score += 2
                    if total_nodes > 5:
                        score += 2
                        health_factors.append("structured")
                    elif total_nodes > 0:
                        score += 1
                        health_factors.append("developing")
            
            # Factor 2: Activity level
            if graph_summary.get('recent_changes'):
                max_score += 2
                changes = len(graph_summary['recent_changes'])
                if 3 <= changes <= 15:  # Sweet spot
                    score += 2
                    health_factors.append("active")
                elif changes > 0:
                    score += 1
                    health_factors.append("some activity")
            
            # Factor 3: External connectivity
            if graph_summary.get('external_links'):
                max_score += 1
                if len(graph_summary['external_links']) > 0:
                    score += 1
                    health_factors.append("connected")
            
            # Factor 4: Concerns level
            concerns = graph_summary.get('concerns', [])
            max_score += 1
            if len(concerns) == 0:
                score += 1
                health_factors.append("stable")
            elif len(concerns) <= 2:
                score += 0.5
                health_factors.append("minor issues")
            
            # Calculate percentage and categorize
            if max_score > 0:
                health_percentage = (score / max_score) * 100
                
                if health_percentage >= 80:
                    health_level = "Excellent"
                elif health_percentage >= 60:
                    health_level = "Good"
                elif health_percentage >= 40:
                    health_level = "Fair"
                else:
                    health_level = "Needs Attention"
                
                return f"{health_level} ({health_percentage:.0f}%) - {', '.join(health_factors)}"
            else:
                return "Insufficient data for assessment"
            
        except Exception:
            return "Health assessment unavailable"
    
    async def _adaptive_learning_update(self, positive: bool, feedback_entry: Dict[str, Any]):
        """Update Navigator behavior based on user feedback patterns."""
        try:
            # Initialize learning weights if not present
            if not hasattr(self, 'learning_weights'):
                self.learning_weights = {
                    'response_length_preference': 0.0,  # Positive = longer, negative = shorter
                    'query_type_success': {},  # Track success rates by query type
                    'provider_performance': {},  # Track performance by AI provider
                    'intervention_timing': 0.0  # Adjust intervention frequency
                }
            
            # Update response length preference
            response_length = feedback_entry.get('response_length', 0)
            if response_length > 0:
                length_factor = 1 if response_length > 300 else -1  # Longer vs shorter responses
                adjustment = 0.1 if positive else -0.1
                self.learning_weights['response_length_preference'] += length_factor * adjustment
                
                # Clamp between -1 and 1
                self.learning_weights['response_length_preference'] = max(-1, min(1, 
                    self.learning_weights['response_length_preference']))
            
            # Update query type success rates
            query_type = feedback_entry.get('query_type', 'unknown')
            if query_type not in self.learning_weights['query_type_success']:
                self.learning_weights['query_type_success'][query_type] = {'positive': 0, 'total': 0}
            
            self.learning_weights['query_type_success'][query_type]['total'] += 1
            if positive:
                self.learning_weights['query_type_success'][query_type]['positive'] += 1
            
            # Update provider performance
            provider = feedback_entry.get('ai_provider', 'unknown')
            if provider not in self.learning_weights['provider_performance']:
                self.learning_weights['provider_performance'][provider] = {'positive': 0, 'total': 0}
            
            self.learning_weights['provider_performance'][provider]['total'] += 1
            if positive:
                self.learning_weights['provider_performance'][provider]['positive'] += 1
            
            # Update intervention timing preference
            intervention_adjustment = 0.05 if positive else -0.05
            self.learning_weights['intervention_timing'] += intervention_adjustment
            self.learning_weights['intervention_timing'] = max(-0.5, min(0.5, 
                self.learning_weights['intervention_timing']))
            
        except Exception as e:
            print(colored(f"Adaptive learning error: {e}", "yellow"))
    
    def get_adaptive_preferences(self) -> Dict[str, Any]:
        """Get current adaptive learning preferences for behavior adjustment."""
        if not hasattr(self, 'learning_weights'):
            return {}
        
        preferences = {}
        
        # Response length preference
        length_pref = self.learning_weights.get('response_length_preference', 0)
        if length_pref > 0.3:
            preferences['preferred_response_length'] = 'longer'
        elif length_pref < -0.3:
            preferences['preferred_response_length'] = 'shorter'
        else:
            preferences['preferred_response_length'] = 'moderate'
        
        # Best performing query types
        query_success = self.learning_weights.get('query_type_success', {})
        best_types = []
        for qtype, stats in query_success.items():
            if stats['total'] >= 3:  # Minimum sample size
                success_rate = stats['positive'] / stats['total']
                if success_rate >= 0.7:
                    best_types.append((qtype, success_rate))
        
        preferences['successful_query_types'] = sorted(best_types, key=lambda x: x[1], reverse=True)
        
        # Provider performance
        provider_perf = self.learning_weights.get('provider_performance', {})
        provider_rates = {}
        for provider, stats in provider_perf.items():
            if stats['total'] >= 2:
                provider_rates[provider] = stats['positive'] / stats['total']
        
        preferences['provider_performance'] = provider_rates
        
        return preferences