#!/usr/bin/env python3
"""
Blue CLI - Jarvis-like workspace-wise pair programming assistant
Built with AutoGen for multi-agent orchestration with transparent decision-making processes.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from termcolor import colored

from agents.navigator import NavigatorAgent
from agents.observer import ObserverAgent
from agents.tool_agents import ToolAgentManager
from core.workspace_graph import WorkspaceGraph
from core.decision_algorithm import DecisionAlgorithm
from core.background_processor import BackgroundProcessor
from utils.config_manager import ConfigManager


class BlueCLI:
    """Main Blue CLI application orchestrating all agents and components."""
    
    def __init__(self, workspace_dir: str, config_path: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.config_manager = ConfigManager(config_path)
        self.workspace_graph = WorkspaceGraph()
        self.decision_algorithm = DecisionAlgorithm()
        
        # Initialize agents
        self.navigator = NavigatorAgent(self.workspace_graph, self.decision_algorithm, self.config_manager)
        self.observer = ObserverAgent(self.workspace_dir)
        self.tool_manager = ToolAgentManager()
        self.background_processor = BackgroundProcessor(self.workspace_dir)
        
        # CLI state
        self.current_goal: Optional[str] = None
        self.verbose_mode = False
        self.quiet_mode = False
        self.show_agent_stream = True  # Show agent observation stream
        self.running = False
        
    async def start(self):
        """Start the Blue CLI interactive session."""
        self.running = True
        
        # Print welcome message
        self._print_welcome()
        
        # Check for API key availability before proceeding
        if not self.config_manager.ensure_ai_provider_available():
            print(colored("\n❌ Cannot start Blue CLI without AI provider API keys.", "red"))
            return
        
        # Load existing graph state if available
        await self._load_graph_state()
        
        # Start observer
        await self.observer.start_watching(self._on_file_change)
        
        # Start background processor silently
        await self.background_processor.start()
        
        # Force user to set a goal before proceeding
        if not self.current_goal:
            await self._force_goal_setting()
        
        # Main interactive loop
        try:
            while self.running:
                await self._interactive_loop()
        except KeyboardInterrupt:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown saving graph state."""
        print(colored("\nShutting down Blue CLI...", "cyan"))
        
        # Save graph state
        await self._save_graph_state()
        
        # Stop observer and background processor
        await self.observer.stop_watching()
        await self.background_processor.stop()
        
        self.running = False
        print(colored("Goodbye!", "green"))
    
    async def _interactive_loop(self):
        """Main interactive command loop."""
        try:
            # Simple approach: prompt for input, but add small sleeps to allow async tasks
            user_input = await self._get_user_input()
            
            # Signal user activity to background processor
            self.background_processor.update_activity()
            
            if not user_input:
                return
            
            await self._process_command(user_input)
            
        except EOFError:
            await self.shutdown()
    
    async def _get_user_input(self):
        """Get user input in a way that doesn't block the event loop completely."""
        import concurrent.futures
        import asyncio
        
        # Run input in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                # Run the blocking input() in a separate thread
                user_input = await loop.run_in_executor(pool, lambda: input(colored("> ", "blue")))
                return user_input.strip()
            except EOFError:
                return None
    
    async def _get_suggestion_response(self):
        """Get user response to suggestion without blocking event loop."""
        import concurrent.futures
        import asyncio
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                response = await loop.run_in_executor(pool, lambda: input(colored("[Y/N/Explain]: ", "yellow")))
                return response.strip().lower()
            except EOFError:
                return None
    
    async def _force_goal_setting(self):
        """Force user to set a goal before proceeding with the session."""
        print(colored("\n🎯 Welcome to Blue CLI! Let's start by setting your programming goal.", "cyan"))
        print(colored("This helps me understand what you're working on and provide better guidance.", "white"))
        
        # Show examples
        print(colored("\nExample goals:", "yellow"))
        examples = [
            "implement user authentication system",
            "refactor database layer for better performance",
            "add real-time notifications to the app",
            "fix memory leaks in the image processing module",
            "migrate from REST API to GraphQL",
            "implement automated testing pipeline"
        ]
        
        for i, example in enumerate(examples[:3], 1):
            print(colored(f"  {i}. {example}", "white"))
        
        print(colored("\nType 'examples' to see more, or 'skip' to use Blue CLI without a specific goal.", "cyan"))
        
        while True:
            try:
                goal_input = await self._get_goal_input()
                
                if not goal_input:
                    continue
                    
                goal_input = goal_input.strip()
                
                if goal_input.lower() == 'examples':
                    self._show_more_goal_examples()
                    continue
                elif goal_input.lower() == 'skip':
                    print(colored("\n⚠️  Proceeding without a specific goal. You can set one later with /set-goal", "yellow"))
                    break
                elif len(goal_input) < 5:
                    print(colored("Please provide a more detailed goal (at least 5 characters)", "red"))
                    continue
                else:
                    # Valid goal provided
                    await self._set_goal(goal_input)
                    print(colored(f"\n✅ Perfect! I'll help you: {goal_input}", "green"))
                    print(colored("\n🚀 Blue CLI is now ready! I'll observe your coding and provide strategic insights.", "cyan"))
                    print(colored("💡 Use /stream on to see file change observations, or just start coding!", "white"))
                    break
                    
            except KeyboardInterrupt:
                print(colored("\n\n⚠️  Goal setting cancelled. Starting Blue CLI without a specific goal.", "yellow"))
                break
            except EOFError:
                print(colored("\n\n⚠️  Input ended. Starting Blue CLI without a specific goal.", "yellow"))
                break
    
    async def _get_goal_input(self):
        """Get goal input from user without blocking event loop."""
        import concurrent.futures
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                prompt = colored("\n🎯 Enter your programming goal: ", "blue")
                goal_input = await loop.run_in_executor(pool, lambda: input(prompt))
                return goal_input.strip()
            except (EOFError, KeyboardInterrupt):
                return None
    
    def _show_more_goal_examples(self):
        """Show additional goal examples to inspire users."""
        print(colored("\n📋 More goal examples:", "cyan"))
        
        examples = [
            "implement user authentication system",
            "refactor database layer for better performance", 
            "add real-time notifications to the app",
            "fix memory leaks in the image processing module",
            "migrate from REST API to GraphQL",
            "implement automated testing pipeline",
            "add dark mode support to the UI",
            "optimize API response times",
            "implement caching layer with Redis",
            "add multi-language support",
            "integrate payment processing",
            "implement role-based access control",
            "add data export functionality",
            "migrate to microservices architecture",
            "implement search functionality",
            "add email notification system"
        ]
        
        categories = {
            "🔧 Development Tasks": examples[:5],
            "🎨 UI/UX Improvements": examples[5:9], 
            "⚡ Performance & Architecture": examples[9:13],
            "📈 Features & Integration": examples[13:]
        }
        
        for category, goal_list in categories.items():
            print(colored(f"\n{category}:", "yellow"))
            for goal in goal_list:
                print(colored(f"  • {goal}", "white"))
    
    async def _process_command(self, command: str):
        """Process user commands."""
        if command.startswith('/'):
            await self._handle_slash_command(command)
        else:
            # Regular query to navigator
            response = await self.navigator.process_query(command, self.current_goal)
            if response:
                print(colored(f"[{datetime.now().strftime('%H:%M')}] Navigator: {response}", "green"))
    
    async def _handle_slash_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(' ', 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/set-goal':
            await self._set_goal(args)
        elif cmd == '/link':
            await self._link_resource(args)
        elif cmd == '/ask':
            await self._ask_navigator(args)
        elif cmd == '/status':
            self._show_status()
        elif cmd == '/quiet':
            self._toggle_quiet_mode()
        elif cmd == '/verbose':
            self._toggle_verbose_mode(args)
        elif cmd == '/stream':
            self._toggle_agent_stream(args)
        elif cmd == '/rate':
            await self._rate_last_suggestion(args)
        elif cmd == '/ai-provider':
            await self._switch_ai_provider(args)
        elif cmd == '/config':
            self._show_config()
        elif cmd == '/background':
            self._show_background_analysis()
        elif cmd == '/trends':
            self._show_tech_trends()
        elif cmd == '/help':
            self._show_help()
        elif cmd == '/exit':
            await self.shutdown()
        else:
            print(colored(f"Unknown command: {cmd}. Type /help for available commands.", "red"))
    
    async def _set_goal(self, goal_text: str):
        """Set or update the current goal."""
        if not goal_text:
            print(colored("Please provide a goal. Usage: /set-goal \"your goal here\"", "yellow"))
            return
        
        # Remove quotes if present
        goal_text = goal_text.strip('\'"')
        
        self.current_goal = goal_text
        await self.navigator.set_goal(goal_text)
        
        print(colored(f"Goal set: {goal_text}", "green"))
        
        # Show goal decomposition
        subtasks = await self.navigator.decompose_goal(goal_text)
        if subtasks:
            print(colored("Sub-tasks:", "cyan"))
            for i, task in enumerate(subtasks, 1):
                print(colored(f"  {i}. {task}", "white"))
    
    async def _link_resource(self, args: str):
        """Link external resources to the workspace graph."""
        parts = args.split(' ', 1)
        if len(parts) != 2:
            print(colored("Usage: /link <type> <url>", "yellow"))
            print(colored("Example: /link jira https://example.atlassian.net/issue/KEY-123", "yellow"))
            return
        
        resource_type, url = parts
        success = await self.workspace_graph.add_external_link(resource_type, url)
        
        if success:
            print(colored(f"Linked {resource_type} resource: {url}", "green"))
        else:
            print(colored(f"Failed to link {resource_type} resource", "red"))
    
    async def _ask_navigator(self, query: str):
        """Ask navigator a direct question."""
        if not query:
            print(colored("Please provide a question. Usage: /ask \"your question\"", "yellow"))
            return
        
        query = query.strip('\'"')
        response = await self.navigator.process_query(query, self.current_goal)
        
        if response:
            print(colored(f"Navigator: {response}", "green"))
    
    def _show_status(self):
        """Show current status and progress."""
        status_lines = [
            f"Goal: {self.current_goal or 'None set'}",
            f"Workspace: {self.workspace_dir}",
            f"Graph nodes: {len(self.workspace_graph.nodes)}",
            f"Graph edges: {len(self.workspace_graph.edges)}",
            f"Strategic score: {self.decision_algorithm.get_current_score()}/{self.decision_algorithm.base_threshold}",
            f"Change momentum: {getattr(self.decision_algorithm, 'change_momentum', 0)}/min",
            f"Verbose mode: {'On' if self.verbose_mode else 'Off'}",
            f"Quiet mode: {'On' if self.quiet_mode else 'Off'}",
            f"Agent stream: {'Visible' if self.show_agent_stream else 'Hidden (observing silently)'}",
            f"Background processor: {'Active' if self.background_processor.is_running else 'Stopped'}",
            f"Idle threshold: {self.background_processor.idle_threshold}s"
        ]
        
        print(colored("=== Blue CLI Status ===", "cyan"))
        for line in status_lines:
            print(colored(line, "white"))
    
    def _toggle_quiet_mode(self):
        """Toggle quiet mode for less frequent interventions."""
        self.quiet_mode = not self.quiet_mode
        self.decision_algorithm.set_quiet_mode(self.quiet_mode)
        
        mode_text = "enabled" if self.quiet_mode else "disabled"
        print(colored(f"Quiet mode {mode_text}", "cyan"))
    
    def _toggle_verbose_mode(self, args: str):
        """Toggle verbose mode for detailed agent dialogues."""
        if args.lower() in ['on', 'true', '1']:
            self.verbose_mode = True
        elif args.lower() in ['off', 'false', '0']:
            self.verbose_mode = False
        else:
            self.verbose_mode = not self.verbose_mode
        
        mode_text = "enabled" if self.verbose_mode else "disabled"
        print(colored(f"Verbose mode {mode_text}", "cyan"))
    
    def _toggle_agent_stream(self, args: str):
        """Toggle agent observation stream visibility."""
        if args.lower() in ['on', 'show', 'true', '1']:
            self.show_agent_stream = True
        elif args.lower() in ['off', 'hide', 'false', '0']:
            self.show_agent_stream = False
        else:
            self.show_agent_stream = not self.show_agent_stream
        
        if self.show_agent_stream:
            status_text = "showing (agent observing and displaying)"
        else:
            status_text = "hidden (agent still observing silently)"
        
        print(colored(f"Agent stream {status_text}", "cyan"))
    
    def _show_background_analysis(self):
        """Show recent background analysis results."""
        print(colored("=== Background Analysis Results ===", "cyan"))
        
        # Get summary
        summary = self.background_processor.get_analysis_summary()
        print(colored(f"Total analyses: {summary['total_analyses']}", "white"))
        print(colored(f"Total findings: {summary['findings']}", "white"))
        print(colored(f"Total recommendations: {summary['recommendations']}", "white"))
        
        if summary['last_analysis']:
            print(colored(f"Last analysis: {summary['last_analysis'].strftime('%H:%M:%S')}", "white"))
        
        # Show recent analyses
        recent = self.background_processor.get_recent_analyses(3)
        if recent:
            print(colored("\nRecent Findings:", "yellow"))
            for analysis in recent:
                print(colored(f"\n{analysis.analysis_type.title()}:", "green"))
                for finding in analysis.findings[:3]:  # Show top 3 findings
                    print(colored(f"  • {finding}", "white"))
                if analysis.recommendations:
                    print(colored(f"  💡 {analysis.recommendations[0]}", "cyan"))
        else:
            print(colored("No background analysis completed yet. Wait for idle periods.", "yellow"))
    
    def _show_tech_trends(self):
        """Show technology trend analysis and recommendations."""
        print(colored("=== Technology Trends & Opportunities ===", "cyan"))
        
        recent = self.background_processor.get_recent_analyses()
        tech_analyses = [a for a in recent if a.analysis_type == "technology_trends"]
        
        if tech_analyses:
            latest = tech_analyses[0]
            print(colored(f"Last updated: {latest.timestamp.strftime('%H:%M:%S')}", "white"))
            
            if latest.findings:
                print(colored("\nModernization Opportunities:", "yellow"))
                for finding in latest.findings:
                    print(colored(f"  🚀 {finding}", "white"))
            
            if latest.recommendations:
                print(colored("\nRecommended Actions:", "green"))
                for rec in latest.recommendations:
                    print(colored(f"  💡 {rec}", "cyan"))
        else:
            print(colored("No technology trend analysis available yet.", "yellow"))
            print(colored("Background analysis will identify modernization opportunities during idle periods.", "white"))
    
    async def _rate_last_suggestion(self, rating: str):
        """Rate the last suggestion for feedback learning."""
        if rating in ['+', 'positive', 'good']:
            await self.navigator.record_feedback(True)
            print(colored("Thanks for the positive feedback!", "green"))
        elif rating in ['-', 'negative', 'bad']:
            await self.navigator.record_feedback(False)
            print(colored("Thanks for the feedback. I'll adjust accordingly.", "yellow"))
        else:
            print(colored("Usage: /rate + or /rate -", "yellow"))
    
    async def _switch_ai_provider(self, provider: str):
        """Switch between OpenAI and Anthropic AI providers."""
        provider = provider.strip().lower()
        
        if not provider:
            current_provider = self.config_manager.get('preferences.ai_provider', 'anthropic')
            available_provider = self.config_manager.get_available_ai_provider()
            print(colored(f"Current AI provider: {current_provider}", "cyan"))
            if available_provider != current_provider:
                print(colored(f"Available provider: {available_provider}", "yellow"))
            print(colored("Usage: /ai-provider openai|anthropic", "yellow"))
            return
        
        if provider not in ['openai', 'anthropic']:
            print(colored("Invalid provider. Use 'openai' or 'anthropic'", "red"))
            return
        
        # Check if API key is available
        api_key = self.config_manager.get_api_key(provider)
        if not api_key:
            env_var = f'{provider.upper()}_API_KEY'
            print(colored(f"{provider.title()} API key not found.", "red"))
            print(colored(f"Set it as environment variable: export {env_var}=your_key_here", "yellow"))
            return
        
        # Update configuration
        self.config_manager.set('preferences.ai_provider', provider)
        
        # Reinitialize navigator with new provider
        self.navigator = NavigatorAgent(self.workspace_graph, self.decision_algorithm, self.config_manager)
        
        print(colored(f"Switched to {provider.title()} AI provider", "green"))
        print(colored("Navigator agent reinitialized with new provider", "cyan"))
    
    def _show_config(self):
        """Show configuration status."""
        self.config_manager.show_status()
    
    def _show_help(self):
        """Show help information."""
        help_text = """
Blue CLI Commands:

  /set-goal "goal"          Set current programming goal
  /set-goal --from jira-456 Set goal from Jira ticket
  /link <type> <url>        Link external resource (jira, github, drive)
  /ask "question"           Ask navigator a question
  /status                   Show current status and progress
  /quiet                    Toggle quiet mode (less interventions)
  /verbose on/off           Toggle verbose mode (show agent dialogues)
  /stream on/off            Toggle agent observation stream display
  /rate +/-                 Rate last suggestion for learning
  /ai-provider <provider>   Switch AI provider (openai/anthropic)
  /config                   Show configuration status
  /background               Show background analysis results
  /trends                   Show technology trend opportunities
  /help                     Show this help message
  /exit                     Exit Blue CLI

Setup:
  Set API keys as environment variables:
    export ANTHROPIC_API_KEY=your_key_here  (recommended)
    export OPENAI_API_KEY=your_key_here

Examples:
  /set-goal "implement user authentication"
  /link jira https://company.atlassian.net/browse/AUTH-123
  /ask "what are the potential blind spots?"
  /ai-provider anthropic
  /verbose on
        """
        print(colored(help_text, "cyan"))
    
    async def _on_file_change(self, event_data: Dict[str, Any]):
        """Handle file change events from observer with stream visualization."""
        try:
            if self.verbose_mode:
                print(colored(f"🔥 Processing: {event_data.get('type', 'unknown')}", "magenta"))
            
            # Signal activity to background processor
            self.background_processor.update_activity()
            
            # Show change stream if enabled
            if self.show_agent_stream:
                print(colored(f"📺 Stream is enabled, displaying change", "cyan"))
                self._display_change_stream(event_data)
            else:
                print(colored(f"🙈 Stream is disabled, not displaying", "yellow"))
            
            # Process event through decision algorithm with detailed output
            decision_details = await self.decision_algorithm.process_event_with_details(
                event_data, self.current_goal, self.workspace_graph
            )
            
            should_intervene = decision_details['should_intervene']
            confidence = decision_details['confidence']
            suggestion = decision_details.get('suggestion')
            
            # Show decision stream if enabled
            if self.show_agent_stream:
                self._display_decision_stream(decision_details, event_data)
            
            if should_intervene:
                timestamp = datetime.now().strftime('%H:%M')
                
                # Generate suggestion using the actual navigator instance
                if not suggestion:
                    print(colored(f"🎯 [{timestamp}] Generating strategic suggestion...", "cyan"))
                    suggestion = await self.navigator.generate_strategic_suggestion(
                        event_data, self.current_goal, decision_details
                    )
                
                if suggestion:
                    print(colored(f"🎯 [{timestamp}] Navigator: {suggestion}", "green"))
                else:
                    print(colored(f"🎯 [{timestamp}] Navigator: Strategic checkpoint - how are we tracking against larger objectives?", "green"))
                
                # Wait for user response
                try:
                    response = await self._get_suggestion_response()
                    if response == 'explain':
                        explanation = await self.navigator.explain_suggestion(suggestion)
                        print(colored(f"Explanation: {explanation}", "cyan"))
                    elif response == 'y':
                        await self.navigator.record_feedback(True)
                    elif response == 'n':
                        await self.navigator.record_feedback(False)
                except (EOFError, KeyboardInterrupt):
                    pass
                    
        except Exception as e:
            print(colored(f"Error processing file change: {e}", "red"))
    
    def _display_change_stream(self, event_data: Dict[str, Any]):
        """Display file change events in the agent observation stream."""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Extract key information from event
            event_type = event_data.get('type', 'unknown')
            src_path = event_data.get('src_path', 'unknown')
            file_name = src_path.split('/')[-1] if '/' in src_path else src_path
            
            # Choose icon and color based on event type
            if event_type == 'created':
                icon = "📄"
                color = "green"
                action = "created"
            elif event_type == 'modified':
                icon = "✏️"
                color = "yellow"
                action = "modified"
            elif event_type == 'deleted':
                icon = "🗑️"
                color = "red"
                action = "deleted"
            elif event_type == 'moved':
                icon = "📁"
                color = "blue"
                action = "moved"
            else:
                icon = "📋"
                color = "white"
                action = event_type
            
            # Display compact stream message
            print(colored(f"  {icon} [{timestamp}] {file_name} {action}", color))
            
            # Show additional context for batch events
            if 'batch_info' in event_data:
                batch = event_data['batch_info']
                event_count = batch.get('event_count', 1)
                if event_count > 1:
                    print(colored(f"    └─ Batch: {event_count} events affecting {len(batch.get('affected_files', []))} files", "cyan"))
                    
        except Exception as e:
            print(colored(f"Stream display error: {e}", "red"))
    
    def _display_decision_stream(self, decision_details: Dict[str, Any], event_data: Dict[str, Any]):
        """Display decision-making process in the agent stream."""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            should_intervene = decision_details.get('should_intervene', False)
            confidence = decision_details.get('confidence', 0)
            total_score = decision_details.get('total_score', 0)
            threshold = decision_details.get('threshold', 0)
            
            # Show decision analysis
            if should_intervene:
                icon = "🤔"
                decision_text = f"Decision: INTERVENE (score: {total_score}/{threshold}, confidence: {confidence:.0f}%)"
                color = "magenta"
            else:
                icon = "👁️"
                score_text = f"{total_score}/{threshold}" if total_score and threshold else "low"
                decision_text = f"Decision: observe (score: {score_text}, confidence: {confidence:.0f}%)"
                color = "blue"
            
            print(colored(f"  {icon} [{timestamp}] {decision_text}", color))
            
            # Show detailed reasoning in verbose mode
            if self.verbose_mode:
                reasoning = decision_details.get('reasoning', '')
                if reasoning:
                    print(colored(f"    └─ Reasoning: {reasoning[:80]}...", "cyan"))
                
                event_score = decision_details.get('event_score', {})
                if event_score:
                    print(colored(f"    └─ Event: {event_score.get('event_type', 'unknown')} " +
                                f"(base: {event_score.get('base_score', 0)}, " +
                                f"final: {event_score.get('final_score', 0)})", "cyan"))
                
                decision_factors = decision_details.get('decision_factors', {})
                if decision_factors:
                    factors_text = f"Events: {decision_factors.get('recent_events_count', 0)}, " + \
                                 f"Last intervention: {decision_factors.get('time_since_last_intervention', 'never')}"
                    print(colored(f"    └─ Context: {factors_text}", "cyan"))
                    
        except Exception as e:
            print(colored(f"Decision stream error: {e}", "red"))
    
    def _print_welcome(self):
        """Print welcome message and basic instructions."""
        welcome_text = f"""
{colored('🔵 Blue CLI - Workspace Pair Programming Assistant', 'blue', attrs=['bold'])}

Workspace: {self.workspace_dir}
Type /help for commands or /exit to quit.
        """
        print(welcome_text)
    
    async def _load_graph_state(self):
        """Load workspace graph state from JSON file."""
        state_file = self.workspace_dir / '.blue_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                await self.workspace_graph.load_state(state_data)
                print(colored("Loaded previous workspace state", "green"))
            except Exception as e:
                print(colored(f"Failed to load state: {e}", "yellow"))
    
    async def _save_graph_state(self):
        """Save workspace graph state to JSON file."""
        state_file = self.workspace_dir / '.blue_state.json'
        try:
            state_data = await self.workspace_graph.get_state()
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            print(colored("Saved workspace state", "green"))
        except Exception as e:
            print(colored(f"Failed to save state: {e}", "yellow"))


def main():
    """Main entry point for Blue CLI."""
    parser = argparse.ArgumentParser(description='Blue CLI - Workspace Pair Programming Assistant')
    parser.add_argument('--dir', required=True, help='Path to codebase directory')
    parser.add_argument('--config', help='Path to configuration TOML file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode')
    parser.add_argument('--quiet', action='store_true', help='Enable quiet mode')
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.dir):
        print(colored(f"Error: Directory '{args.dir}' does not exist", "red"))
        sys.exit(1)
    
    # Create Blue CLI instance
    blue_cli = BlueCLI(args.dir, args.config)
    
    # Set initial modes
    if args.verbose:
        blue_cli.verbose_mode = True
    if args.quiet:
        blue_cli.quiet_mode = True
        blue_cli.decision_algorithm.set_quiet_mode(True)
    
    # Run the CLI
    try:
        asyncio.run(blue_cli.start())
    except KeyboardInterrupt:
        print(colored("\nExiting...", "cyan"))
        sys.exit(0)


if __name__ == "__main__":
    main()