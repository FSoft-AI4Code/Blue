#!/usr/bin/env python3
"""
Provider Switcher Utility - Programmatically switch AI providers for Blue CLI.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import ConfigManager


class ProviderSwitcher:
    """Utility class for programmatically switching AI providers."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.available_providers = ['openai', 'anthropic']
    
    def switch_provider(self, provider: str) -> bool:
        """
        Switch AI provider permanently in config.
        
        Args:
            provider: 'openai' or 'anthropic'
            
        Returns:
            True if successful, False otherwise
        """
        if provider not in self.available_providers:
            print(f"❌ Invalid provider: {provider}")
            print(f"   Available: {', '.join(self.available_providers)}")
            return False
        
        # Check if API key is available
        api_key = self.config_manager.get_api_key(provider)
        if not api_key:
            print(f"❌ {provider.title()} API key not configured")
            print(f"   Set: export {provider.upper()}_API_KEY='your-key'")
            return False
        
        # Update config
        self.config_manager.set('preferences.ai_provider', provider)
        print(f"✅ Switched default AI provider to {provider.title()}")
        return True
    
    def get_current_provider(self) -> str:
        """Get currently configured provider."""
        return self.config_manager.get('preferences.ai_provider', 'anthropic')
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {}
        current = self.get_current_provider()
        
        for provider in self.available_providers:
            api_key = self.config_manager.get_api_key(provider)
            status[provider] = {
                'configured': bool(api_key),
                'active': provider == current,
                'env_var': f"{provider.upper()}_API_KEY"
            }
        
        return status
    
    def show_status(self):
        """Display provider status."""
        print("🔵 Blue CLI AI Provider Status")
        print("=" * 35)
        
        status = self.get_provider_status()
        
        for provider, info in status.items():
            active_marker = "🟢 ACTIVE" if info['active'] else "⚪ inactive"
            config_marker = "✅" if info['configured'] else "❌"
            
            print(f"{config_marker} {provider.title():10} {active_marker}")
            if not info['configured']:
                print(f"   └─ Set: export {info['env_var']}='your-key'")
        
        print()
    
    def auto_switch(self) -> str:
        """
        Automatically switch to best available provider.
        Priority: configured provider > anthropic > openai
        """
        current = self.get_current_provider()
        current_key = self.config_manager.get_api_key(current)
        
        if current_key:
            print(f"✅ Using configured provider: {current.title()}")
            return current
        
        # Try Anthropic first (our preferred default)
        anthropic_key = self.config_manager.get_api_key('anthropic')
        if anthropic_key:
            self.switch_provider('anthropic')
            return 'anthropic'
        
        # Fall back to OpenAI
        openai_key = self.config_manager.get_api_key('openai')
        if openai_key:
            self.switch_provider('openai')
            return 'openai'
        
        print("❌ No API keys configured!")
        print("   Set: export ANTHROPIC_API_KEY='your-key'")
        print("   Or:  export OPENAI_API_KEY='your-key'")
        return current


def main():
    """Command-line interface for provider switching."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Blue CLI AI Provider Switcher')
    parser.add_argument('--switch', choices=['openai', 'anthropic'], 
                       help='Switch to specified provider')
    parser.add_argument('--status', action='store_true', 
                       help='Show provider status')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-switch to best available provider')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    switcher = ProviderSwitcher(args.config)
    
    if args.status:
        switcher.show_status()
    elif args.switch:
        switcher.switch_provider(args.switch)
    elif args.auto:
        provider = switcher.auto_switch()
        print(f"Selected provider: {provider}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()