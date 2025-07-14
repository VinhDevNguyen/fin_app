from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import json
from pathlib import Path
import logging
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    def create_prompt(self, system_prompt: str, user_content: str) -> Dict[str, Any]:
        """Create prompt structure for the LLM."""
        pass
    
    @abstractmethod
    def send_prompt(self, prompt: Dict[str, Any]) -> str:
        """Send prompt to LLM and get response."""
        pass
    
    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            # Try to parse the response directly as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # If direct parsing fails, try to find JSON in the response
            import re
            json_pattern = r'\[[\s\S]*\]'
            match = re.search(json_pattern, response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from response: {response}")
                    raise ValueError("Could not extract valid JSON from response")
            else:
                logger.error(f"No JSON found in response: {response}")
                raise ValueError("No JSON found in response")
    
    def save_result(self, result: Dict[str, Any], output_path: Path) -> None:
        """Save result to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved result to {output_path}")
    
    def process_text_file(
        self, 
        text_content: str, 
        system_prompt_or_id: str, 
        output_path: Path,
        use_prompt_library: bool = True
    ) -> Dict[str, Any]:
        """Process text file through LLM and save result.
        
        Args:
            text_content: The text content to process
            system_prompt_or_id: Either a prompt ID from the library or a direct system prompt
            output_path: Path to save the output JSON
            use_prompt_library: If True, treat system_prompt_or_id as a prompt ID
        """
        if use_prompt_library:
            prompt_manager = PromptManager()
            system_prompt = prompt_manager.get_prompt(system_prompt_or_id)
        else:
            system_prompt = system_prompt_or_id
            
        prompt = self.create_prompt(system_prompt, text_content)
        response = self.send_prompt(prompt)
        result = self.extract_json_from_response(response)
        self.save_result(result, output_path)
        return result