import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages loading and retrieving prompts from the prompt library."""

    def __init__(self, library_path: Optional[Path] = None):
        if library_path is None:
            library_path = Path(__file__).parent / "prompts" / "library.json"
        self.library_path = library_path
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> dict[str, dict[str, str]]:
        """Load prompts from the library file."""
        try:
            with open(self.library_path, encoding="utf-8") as f:
                data: Any = json.load(f)
                return dict(data)
        except FileNotFoundError:
            logger.error(f"Prompt library not found at {self.library_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing prompt library: {e}")
            return {}

    def get_prompt(self, prompt_id: str) -> str:
        """Get a system prompt by ID."""
        if prompt_id not in self.prompts:
            raise ValueError(
                f"Prompt '{prompt_id}' not found in library. Available prompts: {list(self.prompts.keys())}"
            )
        return self.prompts[prompt_id]["system_prompt"]

    def get_prompt_info(self, prompt_id: str) -> dict[str, str]:
        """Get full prompt information by ID."""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt '{prompt_id}' not found in library")
        return self.prompts[prompt_id]

    def list_prompts(self) -> dict[str, dict[str, str]]:
        """List all available prompts with their names and descriptions."""
        return {
            prompt_id: {
                "name": info.get("name", prompt_id),
                "description": info.get("description", "No description"),
            }
            for prompt_id, info in self.prompts.items()
        }
