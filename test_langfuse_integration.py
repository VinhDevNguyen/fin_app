#!/usr/bin/env python3
"""Test script to verify Langfuse integration."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_langfuse_integration():
    """Test Langfuse integration with a simple LLM call."""
    
    # Import after loading env vars
    from infrastructure.llm import LLMFactory
    from config import app_settings
    
    logger.info("Starting Langfuse integration test...")
    
    # Initialize Langfuse if credentials are provided
    if app_settings.langfuse_secret_key and app_settings.langfuse_public_key:
        logger.info("Initializing Langfuse...")
        LLMFactory.initialize_langfuse(
            secret_key=app_settings.langfuse_secret_key,
            public_key=app_settings.langfuse_public_key,
            host=app_settings.langfuse_host
        )
    else:
        logger.warning("Langfuse credentials not found in environment variables")
        logger.info("Please set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in your .env file")
        return
    
    # Create LLM provider
    provider = LLMFactory.create_provider(
        provider_type=app_settings.llm_provider,
        api_key=app_settings.llm_api_key,
        model=app_settings.llm_model,
        temperature=app_settings.llm_temperature
    )
    
    # Test text
    test_text = """
    This is a test transaction:
    Date: 2024-01-15
    Description: Coffee Shop
    Amount: $5.50
    """
    
    # Test system prompt
    test_prompt = """
    Extract transaction details from the text and return as JSON with fields:
    - date
    - description
    - amount
    """
    
    # Process the text
    output_path = Path("test_langfuse_output.json")
    try:
        result = provider.process_text_file(
            text_content=test_text,
            system_prompt_or_id=test_prompt,
            output_path=output_path,
            use_prompt_library=False
        )
        
        logger.info(f"Test successful! Result: {result}")
        logger.info(f"Output saved to: {output_path}")
        
        # Flush Langfuse to ensure trace is sent
        from infrastructure.llm.langfuse_wrapper import LangfuseWrapper
        LangfuseWrapper.flush()
        
        logger.info("Langfuse trace should now be visible in your Langfuse dashboard")
        
        # Clean up
        if output_path.exists():
            output_path.unlink()
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    test_langfuse_integration()