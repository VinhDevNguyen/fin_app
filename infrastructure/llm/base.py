from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Literal, List
import json
from pathlib import Path
from pydantic import BaseModel, Field
import logging
from datetime import datetime
from .prompt_manager import PromptManager
from .langfuse_wrapper import LangfuseWrapper
from .pydantic_models.transactions import TransactionHistory, TransactionEntry

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self):
        self.base_url = None
        self.provider_name = "unknown"
        self.model = "unknown"
        self.temperature = 0.0
    
    @abstractmethod
    def create_prompt(self, system_prompt: str, user_content: str) -> Dict[str, Any]:
        """Create prompt structure for the LLM."""
        pass
    
    @abstractmethod
    def send_prompt(self, prompt: Dict[str, Any], output_format: BaseModel) -> str:
        """Send prompt to LLM and get response."""
        pass
    
    def _send_prompt_with_tracing(self, prompt: Dict[str, Any], trace_name: str, output_format: BaseModel) -> str:
        """Wrapper method to add Langfuse tracing to prompt sending."""
        if LangfuseWrapper.is_initialized():
            langfuse = LangfuseWrapper.get_instance()
            
            # Use context manager for span and generation
            with langfuse.start_as_current_span(
                name=trace_name,
                metadata={
                    "provider": self.provider_name,
                    "model": self.model,
                    "temperature": self.temperature
                }
            ) as span:
                with langfuse.start_as_current_generation(
                    name=f"{self.provider_name}_completion",
                    model=self.model,
                    input=prompt,
                    model_parameters={
                        "temperature": self.temperature,
                        "response_format": "json_object"
                    }
                ) as generation:
                    try:
                        # Call the actual send_prompt method
                        response = self.send_prompt(prompt, output_format)
                        
                        # Update the generation with the output
                        generation.update(output=response)
                        
                        return response
                    except Exception as e:
                        # Log the error to Langfuse
                        generation.update(
                            level="ERROR",
                            status_message=str(e)
                        )
                        raise
        else:
            # If Langfuse is not initialized, just call the method directly
            return self.send_prompt(prompt)
    
    def extract_json_from_response(self, response: list[TransactionEntry]) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            output = []
            for transaction in response:
                output.append({
                    "transaction_date": transaction.transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "transaction_detail": transaction.transaction_detail,
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "category": transaction.category,
                    "receiver": transaction.receiver_name,
                    "service_subscription": transaction.service_subscription
                })
            return {
                "transactions": output
            }
        except:
            logger.error(f"No JSON found in response: {response}")
            raise ValueError("No JSON found in response")
        # try:
        #     # Try to parse the response directly as JSON
        #     return json.loads(response)
        # except json.JSONDecodeError:
        #     # If direct parsing fails, try to find JSON in the response
        #     import re
        #     json_pattern = r'\[[\s\S]*\]'
        #     match = re.search(json_pattern, response)
        #     if match:
        #         try:
        #             return json.loads(match.group())
        #         except json.JSONDecodeError:
        #             logger.error(f"Failed to parse JSON from response: {response}")
        #             raise ValueError("Could not extract valid JSON from response")
        #     else:
        #         logger.error(f"No JSON found in response: {response}")
        #         raise ValueError("No JSON found in response")
    
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
        
        # Use the tracing wrapper for the LLM call
        trace_name = f"process_file_{output_path.name}"
        response = self._send_prompt_with_tracing(prompt, trace_name, TransactionHistory)
        
        result = self.extract_json_from_response(response)
        self.save_result(result, output_path)
        return result