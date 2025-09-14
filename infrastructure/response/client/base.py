import logging
from typing import Any
from abc import ABC, abstractmethod

from openai import OpenAI

class ResponseClient(ABC):
    """Base class for response client"""
    
    def __init__(self) -> None:
        self.base_url: str = None
        self.provider_name = "unknown"
        self.model = "unknown"
        self.temperature = 0.7