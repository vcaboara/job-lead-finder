"""Factory for creating AI provider instances with automatic fallback."""
import logging
import os
from typing import List, Optional

from smf.providers.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """Factory for creating and managing AI provider instances.
    
    Supports automatic fallback between providers (e.g., Ollama -> Gemini -> OpenAI).
    """

    def __init__(self):
        """Initialize the factory."""
        self._providers = {}
        self._provider_order = []

    def register_provider(self, name: str, provider_class: type, priority: int = 0):
        """Register a provider class with the factory.
        
        Args:
            name: Provider name (e.g., 'ollama', 'gemini', 'openai')
            provider_class: Provider class that implements BaseAIProvider
            priority: Priority order (lower = higher priority, 0 = highest)
        """
        self._providers[name] = {"class": provider_class, "priority": priority}
        # Sort by priority
        self._provider_order = sorted(self._providers.keys(), key=lambda k: self._providers[k]["priority"])

    def create_provider(
        self, provider_name: Optional[str] = None, **kwargs
    ) -> Optional[BaseAIProvider]:
        """Create a provider instance.
        
        Args:
            provider_name: Specific provider to create, or None for auto-select
            **kwargs: Arguments to pass to provider constructor
            
        Returns:
            Provider instance, or None if creation fails
        """
        if provider_name:
            # Create specific provider
            if provider_name not in self._providers:
                logger.error(f"Provider '{provider_name}' not registered")
                return None
            
            try:
                provider_class = self._providers[provider_name]["class"]
                provider = provider_class(**kwargs)
                if provider.is_available():
                    logger.info(f"Created provider: {provider_name}")
                    return provider
                else:
                    logger.warning(f"Provider '{provider_name}' not available")
                    return None
            except Exception as e:
                logger.error(f"Failed to create provider '{provider_name}': {e}")
                return None
        else:
            # Auto-select first available provider
            for name in self._provider_order:
                try:
                    provider_class = self._providers[name]["class"]
                    provider = provider_class(**kwargs)
                    if provider.is_available():
                        logger.info(f"Auto-selected provider: {name}")
                        return provider
                except Exception as e:
                    logger.debug(f"Provider '{name}' not available: {e}")
                    continue
            
            logger.error("No available providers")
            return None

    def create_with_fallback(self, preferred_order: Optional[List[str]] = None, **kwargs) -> Optional[BaseAIProvider]:
        """Create a provider with automatic fallback.
        
        Args:
            preferred_order: List of provider names in preference order
            **kwargs: Arguments to pass to provider constructor
            
        Returns:
            First available provider, or None if all fail
        """
        order = preferred_order if preferred_order else self._provider_order
        
        for provider_name in order:
            if provider_name not in self._providers:
                logger.debug(f"Provider '{provider_name}' not registered, skipping")
                continue
            
            provider = self.create_provider(provider_name, **kwargs)
            if provider:
                return provider
        
        logger.error("All providers failed")
        return None

    def get_available_providers(self) -> List[str]:
        """Get list of registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self._provider_order)


# Global factory instance
_global_factory = None


def get_factory() -> AIProviderFactory:
    """Get the global AI provider factory instance.
    
    Returns:
        Global AIProviderFactory instance
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = AIProviderFactory()
        _register_default_providers(_global_factory)
    return _global_factory


def _register_default_providers(factory: AIProviderFactory):
    """Register default providers with the factory.
    
    Args:
        factory: Factory instance to register providers with
    """
    # Try to import and register Ollama provider
    try:
        from app.ollama_provider import OllamaProvider
        factory.register_provider("ollama", OllamaProvider, priority=0)  # Highest priority (free, local)
    except ImportError:
        logger.debug("OllamaProvider not available")
    
    # Try to import and register Gemini provider
    try:
        from app.gemini_provider import GeminiProvider
        factory.register_provider("gemini", GeminiProvider, priority=1)  # Medium priority
    except ImportError:
        logger.debug("GeminiProvider not available")
