from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from typing_extensions import Literal
from contextlib import asynccontextmanager
import logging
from ..llm.pydantic_models.transactions import TransactionEntry

class DatabaseStrategy(ABC):
    """Abstract base class for database strategies"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the database connection and schema"""
        pass
    
    @abstractmethod
    async def add_transaction(self, transaction: TransactionEntry) -> bool:
        """Add a transaction entry to the database"""
        pass
    
    @abstractmethod
    async def get_transactions(self, limit: Optional[int] = None) -> List[TransactionEntry]:
        """Retrieve transaction entries from the database"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connections"""
        pass