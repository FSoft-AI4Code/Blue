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
    """Handles configuration loading with fallback and validation"""
    
    def __init__(self):
        self._config_cache = None
        self._config_paths = [
            "config/config.toml",          # User config
            "blue/config/default.toml",    # Default config
            "config.toml"                  # Legacy location
        ]
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file with fallback to defaults"""
        if self._config_cache is not None:
            return self._config_cache
        
        config = {}
        config_loaded = False
        
        # Try specific path if provided
        if config_path:
            config = self._load_config_file(config_path)
            if config:
                config_loaded = True
                print(colored(f"[CONFIG] Loaded from: {config_path}", "green"))
        
        # Try standard paths
        if not config_loaded:
            for path in self._config_paths:
                if os.path.exists(path):
                    loaded_config = self._load_config_file(path)
                    if loaded_config:
                        config = loaded_config
                        config_loaded = True
                        print(colored(f"[CONFIG] Loaded from: {path}", "green"))
                        break
        
        if not config_loaded:
            print(colored("[CONFIG] No config file found, using built-in defaults", "yellow"))
            config = self._get_default_config()
        
        # Validate and enhance config
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
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and add missing default values"""
        # Ensure required sections exist
        required_sections = ['models', 'system_prompts', 'limits', 'scoring', 'monitoring']
        for section in required_sections:
            if section not in config:
                config[section] = {}
        
        # Validate models section
        if 'anthropic' not in config['models']:
            config['models']['anthropic'] = {}
        if 'openai' not in config['models']:
            config['models']['openai'] = {}
        
        # Add default model settings
        anthropic_defaults = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 400,
            'temperature': 0.7
        }
        openai_defaults = {
            'model': 'gpt-4o',
            'max_tokens': 400,
            'temperature': 0.7,
            'base_url': 'https://api.openai.com/v1'
        }
        
        for key, value in anthropic_defaults.items():
            if key not in config['models']['anthropic']:
                config['models']['anthropic'][key] = value
        
        for key, value in openai_defaults.items():
            if key not in config['models']['openai']:
                config['models']['openai'][key] = value
        
        # Validate limits section
        limits_defaults = {
            'min_buffer_size': 3,
            'buffer_threshold': 4,
            'processing_cooldown': 30,
            'max_conversation_history': 8,
            'max_recent_changes': 6,
            'score_threshold': 5,
            'idle_threshold': 30,
            'max_buffer_age': 120,
            'enable_llm_decision': True,
            'confidence_threshold': 7,
            'enable_adaptive_learning': True,
            'threshold_adjustment': 1,
            'min_score_threshold': 3,
            'max_score_threshold': 10
        }
        
        for key, value in limits_defaults.items():
            if key not in config['limits']:
                config['limits'][key] = value
        
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get minimal default configuration"""
        return {
            'models': {
                'anthropic': {
                    'model': 'claude-3-5-sonnet-20241022',
                    'max_tokens': 400,
                    'temperature': 0.7
                },
                'openai': {
                    'model': 'gpt-4o',
                    'max_tokens': 400,
                    'temperature': 0.7,
                    'base_url': 'https://api.openai.com/v1'
                }
            },
            'system_prompts': {
                'proactive': 'You are Blue, an ambient pair programming assistant. Provide helpful, conversational comments about code changes.',
                'interactive': 'You are Blue, a friendly coding assistant. Have natural conversations with developers.'
            },
            'limits': {
                'min_buffer_size': 3,
                'buffer_threshold': 4,
                'processing_cooldown': 30,
                'max_conversation_history': 8,
                'max_recent_changes': 6,
                'score_threshold': 5,
                'idle_threshold': 30,
                'max_buffer_age': 120,
                'enable_llm_decision': True,
                'confidence_threshold': 7,
                'enable_adaptive_learning': True,
                'threshold_adjustment': 1,
                'min_score_threshold': 3,
                'max_score_threshold': 10,
                'decision_prompt': 'Changes: {changes}. Context: {context}. Good time for big-picture input? Answer: YES/NO, confidence 1-10.'
            },
            'scoring': {},
            'monitoring': {
                'supported_extensions': ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.cs', '.vue', '.html', '.css', '.scss', '.sql', '.yaml', '.yml', '.json'],
                'ignore_directories': ['node_modules', '__pycache__', '.git', 'build', 'dist', 'target', '.pytest_cache', '.vscode', '.idea', 'venv', 'env'],
                'ignore_files': ['.DS_Store', '*.log', '*.tmp', '*.cache']
            }
        }
    
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