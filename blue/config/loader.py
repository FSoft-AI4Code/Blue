"""
Configuration Loader

Handles loading and validation of configuration files for Blue.
"""

import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from termcolor import colored


class ConfigLoader:
    """Handles configuration loading with TOML file fallback system"""
    
    def __init__(self):
        self._config_cache = None
        self._default_config_path = "blue/config/default.toml"
        self._prompts_config_path = "blue/config/prompts.toml"
        self._user_config_paths = [
            "config/config.toml",          # Primary user config location
            "config.toml"                  # Legacy location
        ]
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration with proper fallback hierarchy"""
        if self._config_cache is not None:
            return self._config_cache
        
        # Step 1: Always load defaults first
        default_config = self._load_config_file(self._default_config_path)
        if not default_config:
            raise RuntimeError(f"Critical error: Cannot load default configuration from {self._default_config_path}")
        
        config = default_config.copy()
        
        # Step 1.5: Load system prompts
        prompts_config = self._load_config_file(self._prompts_config_path)
        if prompts_config:
            # Convert prompts structure to legacy format for compatibility
            if 'navigator' in prompts_config:
                config.setdefault('system_prompts', {}).update({
                    'proactive': prompts_config['navigator'].get('proactive', ''),
                    'interactive': prompts_config['navigator'].get('interactive', '')
                })
            if 'intervention' in prompts_config:
                config.setdefault('limits', {})['decision_prompt'] = prompts_config['intervention'].get('decision', '')
        else:
            print(colored(f"[CONFIG] Warning: Could not load prompts from {self._prompts_config_path}", "yellow"))
        
        # Step 2: Override with user configuration if available
        user_config_path = None
        user_config = {}
        
        # Try specific path if provided
        if config_path:
            user_config = self._load_config_file(config_path)
            if user_config:
                user_config_path = config_path
        
        # Try standard user config paths
        if not user_config:
            for path in self._user_config_paths:
                if os.path.exists(path):
                    loaded_config = self._load_config_file(path)
                    if loaded_config:
                        user_config = loaded_config
                        user_config_path = path
                        break
        
        # Step 3: Merge user config over defaults
        if user_config:
            config = self._merge_configs(config, user_config)
            print(colored(f"[CONFIG] Loaded defaults + user overrides from: {user_config_path}", "green"))
        else:
            print(colored("[CONFIG] Using default configuration (no user config found)", "yellow"))
        
        # Step 4: Final validation
        config = self._validate_config(config)
        self._config_cache = config
        return config
    
    def _load_config_file(self, path: str) -> Dict[str, Any]:
        """Load configuration from a specific file"""
        try:
            with open(path, 'r') as f:
                return toml.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(colored(f"[CONFIG] Error loading {path}: {e}", "red"))
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge override config into base config"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Direct override for non-dict values or new keys
                result[key] = value
        
        return result
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Basic validation - ensure required sections exist"""
        required_sections = ['llm_providers', 'agents', 'models', 'system_prompts', 'limits', 'scoring', 'monitoring']
        
        for section in required_sections:
            if section not in config:
                print(colored(f"[CONFIG] Warning: Missing section '{section}' in configuration", "yellow"))
                config[section] = {}
        
        # Validate critical subsections exist
        if 'anthropic' not in config.get('llm_providers', {}):
            config.setdefault('llm_providers', {})['anthropic'] = {}
        if 'openai' not in config.get('llm_providers', {}):
            config.setdefault('llm_providers', {})['openai'] = {}
        
        if 'navigator' not in config.get('agents', {}):
            print(colored("[CONFIG] Warning: Missing 'navigator' agent configuration", "yellow"))
        if 'intervention' not in config.get('agents', {}):
            print(colored("[CONFIG] Warning: Missing 'intervention' agent configuration", "yellow"))
        
        return config
    
    def reload_config(self):
        """Reload configuration from file"""
        self._config_cache = None
        return self.load_config()


# Global config loader instance
_config_loader = ConfigLoader()

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get the current configuration"""
    return _config_loader.load_config(config_path)

def reload_config():
    """Reload configuration from file"""
    return _config_loader.reload_config()