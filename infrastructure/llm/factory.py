from typing import Optional
from .base import LLMProvider
from .openai_provider import OpenAICompatibleProvider
from .gemini_provider import GeminiProvider
from .langfuse_wrapper import LangfuseWrapper


class LLMFactory:
    """Factory class for creating LLM providers."""

    @staticmethod
    def initialize_langfuse(
        secret_key: Optional[str] = None,
        public_key: Optional[str] = None,
        host: Optional[str] = None,
    ):
        """Initialize Langfuse if credentials are provided."""
        LangfuseWrapper.initialize(secret_key, public_key, host)

    @staticmethod
    def create_provider(
        base_url: Optional[str],
        provider_type: str,
        api_key: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
    ) -> LLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_type: Type of provider ('openai' or 'gemini')
            api_key: API key for the provider
            model: Model name (optional, uses default if not provided)
            temperature: Temperature for generation (0.0 for deterministic)

        Returns:
            LLMProvider instance

        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type.lower() == "openai":
            return OpenAICompatibleProvider(
                base_url=base_url,
                api_key=api_key,
                model=model or "gpt-4o-mini",
                temperature=temperature,
            )
        elif provider_type.lower() == "gemini":
            return GeminiProvider(
                base_url=base_url,
                api_key=api_key,
                model=model or "gemini-2.5-flash",
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
