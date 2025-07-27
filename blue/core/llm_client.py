"""
LLM Client Abstraction

Provides unified interface for different LLM providers (Anthropic, OpenAI).
"""

import os
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from termcolor import colored
import anthropic
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: str = "", **kwargs) -> Optional[str]:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the client is properly configured and available"""
        pass


class AnthropicClient(LLMClient):
    """Anthropic Claude client implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> Optional[anthropic.Anthropic]:
        """Initialize Anthropic Claude client"""
        api_key = self.config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            print(colored("Warning: ANTHROPIC_API_KEY not found in config or environment.", "red"))
            return None
        
        try:
            return anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            print(colored(f"Error initializing Anthropic client: {e}", "red"))
            return None
    
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: str = "", **kwargs) -> Optional[str]:
        """Generate response using Anthropic Claude API"""
        if not self.client:
            return None
        
        try:
            model = self.config.get('model', 'claude-3-5-sonnet-20241022')
            max_tokens = kwargs.get('max_tokens', self.config.get('max_tokens', 400))
            temperature = kwargs.get('temperature', self.config.get('temperature', 0.7))
            
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(colored(f"Anthropic API error: {e}", "red"))
            return None
    
    def is_available(self) -> bool:
        """Check if Anthropic client is available"""
        return self.client is not None


class OpenAIClient(LLMClient):
    """OpenAI client implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> Optional[openai.OpenAI]:
        """Initialize OpenAI client"""
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print(colored("Warning: OPENAI_API_KEY not found in config or environment.", "red"))
            return None
        
        try:
            base_url = self.config.get('base_url')
            if base_url:
                return openai.OpenAI(api_key=api_key, base_url=base_url)
            else:
                return openai.OpenAI(api_key=api_key)
        except Exception as e:
            print(colored(f"Error initializing OpenAI client: {e}", "red"))
            return None
    
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: str = "", **kwargs) -> Optional[str]:
        """Generate response using OpenAI API"""
        if not self.client:
            return None
        
        try:
            model = self.config.get('model', 'gpt-4o')
            max_tokens = kwargs.get('max_tokens', self.config.get('max_tokens', 400))
            temperature = kwargs.get('temperature', self.config.get('temperature', 0.7))
            
            # Add system message to the beginning for OpenAI
            api_messages = []
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            api_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=api_messages
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(colored(f"OpenAI API error: {e}", "red"))
            return None
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available"""
        return self.client is not None


class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create_client(provider: str, config: Dict[str, Any]) -> Optional[LLMClient]:
        """Create an LLM client for the specified provider"""
        provider = provider.lower()
        
        if provider == "anthropic":
            return AnthropicClient(config)
        elif provider == "openai":
            return OpenAIClient(config)
        else:
            print(colored(f"Unsupported LLM provider: {provider}", "red"))
            return None
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available LLM providers"""
        return ["anthropic", "openai"]