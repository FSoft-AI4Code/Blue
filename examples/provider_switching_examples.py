#!/usr/bin/env python3
"""
Examples of programmatically switching AI providers in Blue CLI.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.navigator import NavigatorAgent
from core.workspace_graph import WorkspaceGraph
from core.decision_algorithm import DecisionAlgorithm
from utils.config_manager import ConfigManager
from utils.provider_switcher import ProviderSwitcher


async def example_1_direct_navigator_switching():
    """Example 1: Direct switching via Navigator API."""
    print("🔵 Example 1: Direct Navigator Switching")
    print("=" * 40)
    
    # Initialize components
    config_manager = ConfigManager()
    workspace_graph = WorkspaceGraph()
    decision_algorithm = DecisionAlgorithm()
    navigator = NavigatorAgent(workspace_graph, decision_algorithm, config_manager)
    
    print(f"Current provider: {navigator.get_current_provider()}")
    print(f"Available providers: {navigator.get_available_providers()}")
    
    # Switch providers
    success = navigator.switch_ai_provider('openai')
    if success:
        print(f"New provider: {navigator.get_current_provider()}")
    
    # Switch back
    navigator.switch_ai_provider('anthropic')
    print(f"Final provider: {navigator.get_current_provider()}")
    print()


def example_2_config_based_switching():
    """Example 2: Config-based switching."""
    print("🔵 Example 2: Config-Based Switching")
    print("=" * 35)
    
    switcher = ProviderSwitcher()
    
    # Show current status
    switcher.show_status()
    
    # Switch provider
    switcher.switch_provider('anthropic')
    
    # Show updated status
    print("After switching:")
    switcher.show_status()


def example_3_environment_based_switching():
    """Example 3: Environment variable detection."""
    print("🔵 Example 3: Environment-Based Switching")
    print("=" * 42)
    
    switcher = ProviderSwitcher()
    
    # Auto-detect best provider
    provider = switcher.auto_switch()
    print(f"Auto-selected provider: {provider}")
    
    status = switcher.get_provider_status()
    for provider, info in status.items():
        print(f"{provider}: configured={info['configured']}, active={info['active']}")
    print()


async def example_4_dynamic_switching_in_session():
    """Example 4: Dynamic switching during operation."""
    print("🔵 Example 4: Dynamic Session Switching")
    print("=" * 38)
    
    # Initialize navigator
    config_manager = ConfigManager()
    workspace_graph = WorkspaceGraph()
    decision_algorithm = DecisionAlgorithm()
    navigator = NavigatorAgent(workspace_graph, decision_algorithm, config_manager)
    
    # Test queries with different providers
    test_query = "What are best practices for API design?"
    
    for provider in ['anthropic', 'openai']:
        print(f"\n--- Testing with {provider.title()} ---")
        
        # Switch provider
        success = navigator.switch_ai_provider(provider)
        if not success:
            print(f"Skipping {provider} - not configured")
            continue
        
        # Test a query (would make actual API call if keys are set)
        print(f"Provider: {navigator.get_current_provider()}")
        print(f"Model: {navigator.model_config['model']}")
        
        # In real usage, you'd do:
        # response = await navigator.process_query(test_query)
        # print(f"Response: {response[:100]}...")
    
    print()


def example_5_provider_comparison():
    """Example 5: Provider comparison utility."""
    print("🔵 Example 5: Provider Comparison")
    print("=" * 32)
    
    config_manager = ConfigManager()
    
    providers_info = {
        'anthropic': {
            'model': 'claude-3-5-sonnet-20241022',
            'context_window': '200K tokens',
            'strengths': ['Long context', 'Code analysis', 'Reasoning'],
            'api_cost': 'Low'
        },
        'openai': {
            'model': 'gpt-4',
            'context_window': '8K tokens',
            'strengths': ['General knowledge', 'Creative tasks', 'Established'],
            'api_cost': 'Medium'
        }
    }
    
    print("Provider Comparison:")
    for provider, info in providers_info.items():
        configured = bool(config_manager.get_api_key(provider))
        status = "✅ Ready" if configured else "❌ Needs API key"
        
        print(f"\n{provider.title()} {status}")
        print(f"  Model: {info['model']}")
        print(f"  Context: {info['context_window']}")
        print(f"  Strengths: {', '.join(info['strengths'])}")
        print(f"  Cost: {info['api_cost']}")
    
    print()


class ProviderManager:
    """Advanced provider management class."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.switcher = ProviderSwitcher()
        self.navigator = None
    
    async def initialize_navigator(self):
        """Initialize navigator with current provider."""
        workspace_graph = WorkspaceGraph()
        decision_algorithm = DecisionAlgorithm()
        self.navigator = NavigatorAgent(workspace_graph, decision_algorithm, self.config_manager)
    
    async def smart_switch(self, task_type: str) -> str:
        """
        Intelligently switch provider based on task type.
        
        Args:
            task_type: 'code_analysis', 'creative', 'reasoning', 'general'
        """
        if not self.navigator:
            await self.initialize_navigator()
        
        # Provider recommendations by task type
        recommendations = {
            'code_analysis': 'anthropic',  # Better at code understanding
            'reasoning': 'anthropic',      # Strong logical reasoning  
            'creative': 'openai',          # Creative writing tasks
            'general': 'anthropic'         # Default choice
        }
        
        recommended = recommendations.get(task_type, 'anthropic')
        
        # Check if recommended provider is available
        api_key = self.config_manager.get_api_key(recommended)
        if api_key:
            success = self.navigator.switch_ai_provider(recommended)
            if success:
                print(f"🎯 Switched to {recommended.title()} for {task_type} task")
                return recommended
        
        # Fallback to any available provider
        for provider in ['anthropic', 'openai']:
            if self.config_manager.get_api_key(provider):
                self.navigator.switch_ai_provider(provider)
                print(f"📋 Using {provider.title()} as fallback")
                return provider
        
        print("❌ No providers available")
        return 'none'
    
    def get_usage_stats(self) -> dict:
        """Get provider usage statistics."""
        # In a real implementation, you'd track API calls
        return {
            'total_requests': 42,
            'anthropic_requests': 30,
            'openai_requests': 12,
            'cost_estimate': '$2.50'
        }


async def example_6_advanced_management():
    """Example 6: Advanced provider management."""
    print("🔵 Example 6: Advanced Provider Management")
    print("=" * 44)
    
    manager = ProviderManager()
    
    # Smart switching based on task type
    for task in ['code_analysis', 'creative', 'reasoning']:
        provider = await manager.smart_switch(task)
        print(f"Task: {task} → Provider: {provider}")
    
    # Usage stats
    stats = manager.get_usage_stats()
    print(f"\nUsage Stats: {stats}")
    print()


async def main():
    """Run all examples."""
    print("🔵 Blue CLI Provider Switching Examples")
    print("=" * 42)
    print()
    
    # Run examples
    await example_1_direct_navigator_switching()
    example_2_config_based_switching()
    example_3_environment_based_switching()
    await example_4_dynamic_switching_in_session()
    example_5_provider_comparison()
    await example_6_advanced_management()
    
    print("✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())