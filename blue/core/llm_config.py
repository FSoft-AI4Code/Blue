"""
LLM Configuration Manager

Handles agent-specific LLM configurations and provides unified client creation.
Supports per-agent provider selection and model configuration for cost optimization.
"""

import os
from typing import Dict, Any, Optional
from termcolor import colored

from .llm_client import LLMClientFactory, LLMClient


class LLMConfigManager:
    """Manages LLM configurations for different agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client_cache: Dict[str, LLMClient] = {}
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get the complete LLM configuration for a specific agent"""
        # Get agent-specific config
        agent_config = self.config.get('agents', {}).get(agent_name, {})
        
        if not agent_config:
            # Fallback to legacy configuration structure
            print(colored(f"[LLM_CONFIG] No agent-specific config for '{agent_name}', using fallback", "yellow"))
            return self._get_fallback_config(agent_name)
        
        provider = agent_config.get('provider', 'anthropic')
        
        # Get provider-specific API keys and settings
        provider_config = self.config.get('llm_providers', {}).get(provider, {})
        
        # Merge provider config with agent-specific settings
        merged_config = {
            'api_key': provider_config.get('api_key', ''),
            'base_url': provider_config.get('base_url', ''),
            'model': agent_config.get('model', self._get_default_model(provider)),
            'max_tokens': agent_config.get('max_tokens', 400),
            'temperature': agent_config.get('temperature', 0.7)
        }
        
        return {
            'provider': provider,
            'config': merged_config
        }
    
    def create_client_for_agent(self, agent_name: str) -> Optional[LLMClient]:
        """Create an LLM client for a specific agent"""
        # Check cache first
        cache_key = f"agent_{agent_name}"
        if cache_key in self.client_cache:
            return self.client_cache[cache_key]
        
        # Get agent configuration
        agent_llm_config = self.get_agent_config(agent_name)
        provider = agent_llm_config['provider']
        config = agent_llm_config['config']
        
        # Create client
        client = LLMClientFactory.create_client(provider, config)
        
        if client:
            self.client_cache[cache_key] = client
            model_info = config.get('model', 'unknown')
            print(colored(f"[LLM_CONFIG] Created {provider.upper()} client for {agent_name} agent (model: {model_info})", "green"))
        else:
            print(colored(f"[LLM_CONFIG] Failed to create {provider.upper()} client for {agent_name} agent", "red"))
        
        return client
    
    def get_client_for_agent(self, agent_name: str) -> Optional[LLMClient]:
        """Get or create an LLM client for a specific agent"""
        return self.create_client_for_agent(agent_name)
    
    def _get_fallback_config(self, agent_name: str) -> Dict[str, Any]:
        """Get fallback configuration when agent-specific config is not available"""
        # Default to anthropic for all agents if no specific config
        provider = 'anthropic'
        
        # Try to get from legacy models config
        models_config = self.config.get('models', {})
        provider_config = models_config.get(provider, {})
        
        if not provider_config:
            # Use built-in defaults
            provider_config = {
                'model': self._get_default_model(provider),
                'max_tokens': 400,
                'temperature': 0.7
            }
        
        # Add API key from environment or legacy config
        api_key = provider_config.get('api_key', '') or os.getenv(f'{provider.upper()}_API_KEY', '')
        provider_config['api_key'] = api_key
        
        return {
            'provider': provider,
            'config': provider_config
        }
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for a provider"""
        defaults = {
            'anthropic': 'claude-3-5-sonnet-20241022',
            'openai': 'gpt-4o'
        }
        return defaults.get(provider, 'claude-3-5-sonnet-20241022')
    
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """Get information about an agent's LLM configuration"""
        agent_config = self.get_agent_config(agent_name)
        config = agent_config['config']
        
        return {
            'agent_name': agent_name,
            'provider': agent_config['provider'],
            'model': config.get('model', 'unknown'),
            'max_tokens': config.get('max_tokens', 400),
            'temperature': config.get('temperature', 0.7),
            'has_api_key': bool(config.get('api_key', '')),
            'client_available': self.get_client_for_agent(agent_name) is not None
        }
    
    def list_agent_configurations(self) -> Dict[str, Dict[str, Any]]:
        """List all configured agents and their settings"""
        agents = {}
        
        # Get from agent-specific configs
        agent_configs = self.config.get('agents', {})
        for agent_name in agent_configs.keys():
            agents[agent_name] = self.get_agent_info(agent_name)
        
        # Add common agents if not explicitly configured
        common_agents = ['navigator', 'intervention']
        for agent_name in common_agents:
            if agent_name not in agents:
                agents[agent_name] = self.get_agent_info(agent_name)
        
        return agents
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the LLM configuration and return status"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'agent_status': {}
        }
        
        # Check each agent configuration
        agents = self.list_agent_configurations()
        
        for agent_name, info in agents.items():
            agent_status = {
                'configured': True,
                'has_api_key': info['has_api_key'],
                'client_available': info['client_available']
            }
            
            if not info['has_api_key']:
                warning = f"Agent '{agent_name}' using {info['provider']} has no API key configured"
                validation_results['warnings'].append(warning)
                agent_status['configured'] = False
            
            if not info['client_available']:
                error = f"Agent '{agent_name}' LLM client could not be created"
                validation_results['errors'].append(error)
                validation_results['valid'] = False
            
            validation_results['agent_status'][agent_name] = agent_status
        
        return validation_results
    
    def clear_cache(self):
        """Clear the client cache (useful for reconfiguration)"""
        self.client_cache.clear()
        print(colored("[LLM_CONFIG] Client cache cleared", "yellow"))