"""Base AI provider interface for standardized provider implementations."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional


class BaseAIProvider(ABC):
    """Abstract base class for AI providers.

    All providers should inherit from this class and implement the required methods.
    This ensures a consistent interface across different AI services (Ollama, Gemini, OpenAI, etc.).
    """

    @abstractmethod
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, request_timeout: int = 90):
        """Initialize the provider.

        Args:
            api_key: Optional API key for the provider (if required)
            model: Model name to use
            request_timeout: Request timeout in seconds
        """
        pass

    @abstractmethod
    def query(self, prompt: str, **options: Any) -> str:
        """Execute a query against the AI model.

        Args:
            prompt: The prompt text to send to the model
            **options: Additional provider-specific options (temperature, max_tokens, etc.)

        Returns:
            The model's response text

        Raises:
            Exception: If the query fails
        """
        pass

    @abstractmethod
    def evaluate(self, item: Dict[str, Any], profile_text: str) -> Dict[str, Any]:
        """Evaluate an item-profile match.

        Args:
            item: Item dictionary (e.g., job, patent, grant) with relevant fields
            profile_text: Profile text (e.g., resume, IP portfolio, research profile)

        Returns:
            Dict with 'score' (0-100) and 'reasoning'

        Raises:
            Exception: If evaluation fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured correctly.

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    def stream(self, prompt: str, **options: Any) -> Iterator[str]:
        """Stream responses from the AI model (optional).

        Args:
            prompt: The prompt text to send to the model
            **options: Additional provider-specific options

        Yields:
            Response chunks as they arrive

        Raises:
            NotImplementedError: If streaming is not supported by this provider
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider.

        Returns:
            Dict with status information:
                - available (bool): Whether provider is available
                - model (str): Current model name
                - latency_ms (int): Response time for health check (if available)
                - error (str): Error message if unavailable
        """
        try:
            available = self.is_available()
            return {
                "available": available,
                "model": getattr(self, "model", "unknown"),
                "error": None if available else "Provider not available",
            }
        except Exception as e:
            return {"available": False, "model": getattr(self, "model", "unknown"), "error": str(e)}
