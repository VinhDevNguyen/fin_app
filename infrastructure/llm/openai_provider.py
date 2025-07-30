import logging
from typing import Any

from openai import OpenAI

from .base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(
        self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.0
    ):
        super().__init__()
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.provider_name = "openai"
        logger.info(f"Initialized OpenAI provider with model: {model}")

    def create_prompt(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Create prompt structure for OpenAI."""
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        }

    def send_prompt(self, prompt: dict[str, Any]) -> str:
        """Send prompt to OpenAI and get response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt["messages"],
                temperature=self.temperature,
                response_format={"type": "json_object"},  # Force JSON response
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
