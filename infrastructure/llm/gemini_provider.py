import logging
from typing import Any

from google import genai
from google.genai import types

from .base import LLMProvider, TransactionHistory

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation."""

    def __init__(
        self, api_key: str, model: str = "gemini-2.5-flash", temperature: float = 0.0
    ):
        super().__init__()
        # Initialize client with API key
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

    def send_prompt(self, prompt: dict[str, Any]) -> str:
        """Send prompt to Gemini and get response."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt["prompt"],
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    response_mime_type="application/json",  # Force JSON response
                    response_schema=TransactionHistory,
                ),
            )
            # Convert the parsed response to JSON string to match base class interface
            if response.parsed and hasattr(response.parsed, "transactions"):
                import json

                result = {
                    "transactions": [
                        {
                            "transaction_date": t.transaction_date.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "transaction_detail": t.transaction_detail,
                            "amount": t.amount,
                            "currency": t.currency,
                            "category": t.category,
                            "receiver_name": t.receiver_name,
                            "service_subscription": t.service_subscription,
                        }
                        for t in response.parsed.transactions
                    ]
                }
                return json.dumps(result)
            else:
                # Fallback to text response if parsing fails
                return response.text or ""
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
