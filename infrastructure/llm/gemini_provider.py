import logging
from typing import Any, Union

from google import genai
from google.genai import types

from .base import LLMProvider
from .pydantic_models.transactions import TransactionHistory

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation."""

    def __init__(
        self,
        base_url: Union[str, None],
        api_key: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.0,
    ):
        super().__init__()
        self.base_url = base_url
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.provider_name = "gemini"
        logger.info(f"Initialized Gemini provider with model: {model}")

    def create_prompt(self, system_prompt: str, user_content: str) -> dict[str, Any]:
        """Create prompt structure for Gemini."""
        # Gemini doesn't have explicit system/user roles, so we combine them
        combined_prompt = (
            f"{system_prompt}\n\nTransaction Contents Text:\n{user_content}"
        )
        return {"prompt": combined_prompt}

    def send_prompt(
        self,
        prompt: dict[str, Any],
        output_format: type[TransactionHistory] = TransactionHistory,
    ) -> TransactionHistory:
        """Send prompt to Gemini and get response."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt["prompt"],
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    response_mime_type="application/json",  # Force JSON response
                    response_schema=output_format,
                ),
            )
            # Return the parsed response directly as TransactionHistory
            if response.parsed and hasattr(response.parsed, "transactions"):
                if isinstance(response.parsed, TransactionHistory):
                    return response.parsed
                else:
                    # Handle case where parsed is not TransactionHistory
                    return TransactionHistory(transactions=[])
            else:
                # Fallback: create empty TransactionHistory if parsing fails
                return TransactionHistory(transactions=[])
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
