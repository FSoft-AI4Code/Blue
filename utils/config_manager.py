"""
Configuration Manager - Handle TOML configuration, API keys, and security.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from termcolor import colored
import getpass

# Use tomllib for Python 3.11+ (built-in), tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


class ConfigManager:
    """
    Manages Blue CLI configuration including:
    - API keys and tokens for external services
    - User preferences and settings
    - Security and encryption for sensitive data
    
    Uses TOML format for configuration files.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self.encrypted_fields = {'api_keys', 'tokens', 'credentials'}
        
        # Load configuration
        self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        # Use XDG config directory on Unix systems, or user home directory
        if os.name == 'posix':
            config_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
        else:
            config_dir = Path.home()
        
        config_dir = config_dir / 'blue-cli'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        return config_dir / 'config.toml'
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'rb') as f:
                    self.config = tomllib.load(f)
                print(colored(f"Loaded config from {self.config_path}", "green"))
            else:
                # Create default configuration
                self.config = self._get_default_config()
                self._save_config()
                print(colored(f"Created default config at {self.config_path}", "green"))
        
        except Exception as e:
            print(colored(f"Error loading config: {e}", "red"))
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'api_keys': {
                'openai': None,
                'anthropic': None,
                'jira': None,
                'github': None,
                'google': None
            },
            'preferences': {
                'verbose_mode': False,
                'quiet_mode': False,
                'intervention_threshold': 8,
                'confidence_threshold': 70.0,
                'buffer_size': 10,
                'ai_provider': 'anthropic'  # Default to Anthropic, can be 'anthropic' or 'openai'
            },
            'integrations': {
                'jira': {
                    'enabled': False,
                    'base_url': None,
                    'username': None
                },
                'github': {
                    'enabled': False,
                    'username': None,
                    'repositories': []
                },
                'google_drive': {
                    'enabled': False,
                    'folder_ids': []
                }
            },
            'security': {
                'encrypt_sensitive_data': True,
                'require_confirmation_for_api_calls': True
            }
        }
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'wb') as f:
                tomli_w.dump(self.config, f)
            
            # Set restrictive permissions for security
            os.chmod(self.config_path, 0o600)
            
        except Exception as e:
            print(colored(f"Error saving config: {e}", "red"))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        config_ref = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        # Set the value
        config_ref[keys[-1]] = value
        
        # Save immediately for important settings
        self._save_config()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service from config file or environment variables."""
        # First check config file
        api_key = self.get(f'api_keys.{service}')
        
        if not api_key:
            # Try environment variable
            env_var = f'{service.upper()}_API_KEY'
            api_key = os.environ.get(env_var)
        
        return api_key
    
    def get_available_ai_provider(self) -> Optional[str]:
        """Get the first available AI provider based on configured API keys."""
        # Check current preference first
        preferred_provider = self.get('preferences.ai_provider', 'anthropic')
        if self.get_api_key(preferred_provider):
            return preferred_provider
        
        # Fall back to other providers
        providers = ['anthropic', 'openai']
        for provider in providers:
            if self.get_api_key(provider):
                return provider
        
        return None
    
    def ensure_ai_provider_available(self) -> bool:
        """Ensure at least one AI provider is available, with helpful error messages."""
        available_provider = self.get_available_ai_provider()
        
        if not available_provider:
            print(colored("\n⚠️  No AI provider API keys found!", "yellow"))
            print(colored("Blue CLI requires either Anthropic or OpenAI API keys to function.", "white"))
            print(colored("\nTo set up API keys, use one of these methods:", "cyan"))
            print(colored("  1. Environment variables (recommended):", "white"))
            print(colored("     export ANTHROPIC_API_KEY=your_key_here", "green"))
            print(colored("     export OPENAI_API_KEY=your_key_here", "green"))
            print(colored("  2. Add to config file at:", "white"))
            print(colored(f"     {self.config_path}", "yellow"))
            print(colored("\nRestart Blue CLI after setting your API key.", "white"))
            return False
        
        # Update preference to available provider if different
        current_provider = self.get('preferences.ai_provider', 'anthropic')
        if available_provider != current_provider:
            self.set('preferences.ai_provider', available_provider)
            print(colored(f"Using {available_provider.title()} as AI provider", "green"))
        
        return True
    
    def setup_integration(self, integration_type: str) -> bool:
        """Interactive setup for an integration."""
        print(colored(f"\n=== Setting up {integration_type.title()} Integration ===", "cyan"))
        
        if integration_type == 'jira':
            return self._setup_jira()
        elif integration_type == 'github':
            return self._setup_github()
        elif integration_type == 'google_drive':
            return self._setup_google_drive()
        else:
            print(colored(f"Unknown integration type: {integration_type}", "red"))
            return False
    
    def _setup_jira(self) -> bool:
        """Setup Jira integration."""
        try:
            print("Please provide your Jira configuration:")
            
            base_url = input("Jira base URL (e.g., https://company.atlassian.net): ").strip()
            if not base_url:
                print(colored("Base URL is required", "red"))
                return False
            
            username = input("Jira username/email: ").strip()
            if not username:
                print(colored("Username is required", "red"))
                return False
            
            # Get API token
            api_token = getpass.getpass("Jira API token (create at id.atlassian.com): ")
            if not api_token.strip():
                print(colored("API token is required", "red"))
                return False
            
            # Save configuration
            self.set('integrations.jira.enabled', True)
            self.set('integrations.jira.base_url', base_url)
            self.set('integrations.jira.username', username)
            self.set('api_keys.jira', api_token.strip())
            
            print(colored("Jira integration configured successfully!", "green"))
            return True
            
        except KeyboardInterrupt:
            print(colored("\nJira setup cancelled.", "yellow"))
            return False
        except Exception as e:
            print(colored(f"Error setting up Jira: {e}", "red"))
            return False
    
    def _setup_github(self) -> bool:
        """Setup GitHub integration."""
        try:
            print("Please provide your GitHub configuration:")
            
            username = input("GitHub username: ").strip()
            if not username:
                print(colored("Username is required", "red"))
                return False
            
            # Get personal access token
            token = getpass.getpass("GitHub personal access token: ")
            if not token.strip():
                print(colored("Personal access token is required", "red"))
                return False
            
            # Optional: repositories to monitor
            repos_input = input("Repositories to monitor (comma-separated, optional): ").strip()
            repositories = [repo.strip() for repo in repos_input.split(',') if repo.strip()]
            
            # Save configuration
            self.set('integrations.github.enabled', True)
            self.set('integrations.github.username', username)
            self.set('integrations.github.repositories', repositories)
            self.set('api_keys.github', token.strip())
            
            print(colored("GitHub integration configured successfully!", "green"))
            return True
            
        except KeyboardInterrupt:
            print(colored("\nGitHub setup cancelled.", "yellow"))
            return False
        except Exception as e:
            print(colored(f"Error setting up GitHub: {e}", "red"))
            return False
    
    def _setup_google_drive(self) -> bool:
        """Setup Google Drive integration."""
        try:
            print("Google Drive integration requires OAuth setup.")
            print("Please follow the instructions at: https://developers.google.com/drive/api/quickstart/python")
            
            credentials_path = input("Path to credentials.json file: ").strip()
            if not credentials_path or not Path(credentials_path).exists():
                print(colored("Valid credentials file is required", "red"))
                return False
            
            # Optional: specific folder IDs to monitor
            folders_input = input("Folder IDs to monitor (comma-separated, optional): ").strip()
            folder_ids = [folder.strip() for folder in folders_input.split(',') if folder.strip()]
            
            # Save configuration
            self.set('integrations.google_drive.enabled', True)
            self.set('integrations.google_drive.credentials_path', credentials_path)
            self.set('integrations.google_drive.folder_ids', folder_ids)
            
            print(colored("Google Drive integration configured successfully!", "green"))
            return True
            
        except KeyboardInterrupt:
            print(colored("\nGoogle Drive setup cancelled.", "yellow"))
            return False
        except Exception as e:
            print(colored(f"Error setting up Google Drive: {e}", "red"))
            return False
    
    def is_integration_enabled(self, integration_type: str) -> bool:
        """Check if an integration is enabled and properly configured."""
        enabled = self.get(f'integrations.{integration_type}.enabled', False)
        
        if not enabled:
            return False
        
        # Check if required configuration is present
        if integration_type == 'jira':
            return all([
                self.get('integrations.jira.base_url'),
                self.get('integrations.jira.username'),
                self.get('api_keys.jira')
            ])
        elif integration_type == 'github':
            return all([
                self.get('integrations.github.username'),
                self.get('api_keys.github')
            ])
        elif integration_type == 'google_drive':
            return self.get('integrations.google_drive.credentials_path') is not None
        
        return False
    
    def get_integration_config(self, integration_type: str) -> Dict[str, Any]:
        """Get configuration for a specific integration."""
        base_config = self.get(f'integrations.{integration_type}', {})
        
        # Add API key if available
        api_key = self.get(f'api_keys.{integration_type}')
        if api_key:
            base_config['api_key'] = api_key
        
        return base_config
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check AI provider configuration
        ai_provider = self.get('preferences.ai_provider', 'openai')
        if ai_provider not in ['openai', 'anthropic']:
            issues.append("Invalid ai_provider (must be 'openai' or 'anthropic')")
        
        # Check if at least one AI API key is available
        available_provider = self.get_available_ai_provider()
        if not available_provider:
            issues.append("No AI provider API keys found - set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
        
        # Check enabled integrations
        for integration in ['jira', 'github', 'google_drive']:
            if self.get(f'integrations.{integration}.enabled', False):
                if not self.is_integration_enabled(integration):
                    issues.append(f"{integration.title()} integration enabled but not properly configured")
        
        # Check preference values
        threshold = self.get('preferences.intervention_threshold', 8)
        if not isinstance(threshold, int) or threshold < 1 or threshold > 20:
            issues.append("Invalid intervention_threshold (must be integer between 1-20)")
        
        confidence = self.get('preferences.confidence_threshold', 70.0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
            issues.append("Invalid confidence_threshold (must be number between 0-100)")
        
        return issues
    
    def show_status(self):
        """Display current configuration status."""
        print(colored("=== Blue CLI Configuration Status ===", "cyan"))
        
        # API Keys
        print(colored("\nAPI Keys:", "yellow"))
        ai_provider = self.get('preferences.ai_provider', 'openai')
        for service in ['openai', 'anthropic', 'jira', 'github', 'google']:
            key = self.get(f'api_keys.{service}')
            status = "✓ Configured" if key else "✗ Not set"
            color = "green" if key else "red"
            
            # Highlight the active AI provider
            service_name = service.title()
            if service in ['openai', 'anthropic']:
                if service == ai_provider:
                    service_name += " (Active AI Provider)"
                else:
                    service_name += " (Inactive)"
            
            print(colored(f"  {service_name}: {status}", color))
        
        # Integrations
        print(colored("\nIntegrations:", "yellow"))
        for integration in ['jira', 'github', 'google_drive']:
            enabled = self.is_integration_enabled(integration)
            status = "✓ Enabled & Configured" if enabled else "✗ Disabled/Not configured"
            color = "green" if enabled else "red"
            print(colored(f"  {integration.replace('_', ' ').title()}: {status}", color))
        
        # Preferences
        print(colored("\nPreferences:", "yellow"))
        prefs = self.get('preferences', {})
        for key, value in prefs.items():
            print(colored(f"  {key}: {value}", "white"))
        
        # Validation
        issues = self.validate_config()
        if issues:
            print(colored("\nConfiguration Issues:", "red"))
            for issue in issues:
                print(colored(f"  • {issue}", "red"))
        else:
            print(colored("\n✓ Configuration is valid", "green"))
    
    @property
    def config_dict(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self.config.copy()