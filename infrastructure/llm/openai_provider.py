import logging
from typing import Any

from openai import OpenAI

from .base import LLMProvider
from .pydantic_models.transactions import TransactionHistory

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ):
        super().__init__()
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.provider_name = "openai"
        logger.info(f"Initialized OpenAICompatible provider with model: {model}")

    def create_prompt(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Create prompt structure for OpenAI."""
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        }

    def send_prompt(
        self,
        prompt: dict[str, Any],
        output_format: type[TransactionHistory] = TransactionHistory,
    ) -> TransactionHistory:
        """Send prompt to OpenAI and get response."""
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=prompt["messages"],
                temperature=self.temperature,
                text_format=output_format,
            )
            result: TransactionHistory = response.output_parsed
            return result
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
