from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from typing_extensions import Literal
from contextlib import asynccontextmanager
import logging
import asyncpg
from ..llm.pydantic_models.transactions import TransactionEntry
from .base_database import DatabaseStrategy
from dotenv import load_dotenv
import os

load_dotenv()


class PostgreSQLStrategy(DatabaseStrategy):
    """PostgreSQL implementation of the database strategy"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool and create schema"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string, min_size=1, max_size=10, command_timeout=60
            )

            # Create the transactions table
            await self._create_schema()
            self.logger.info("PostgreSQL strategy initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL strategy: {e}")
            raise

    async def _create_schema(self) -> None:
        """Create the transactions table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
            transaction_detail TEXT NOT NULL,
            amount VARCHAR(50) NOT NULL,
            currency VARCHAR(10) NOT NULL,
            category VARCHAR(50) NOT NULL,
            service_subscription VARCHAR(100),
            receiver_name VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create index on transaction_date for faster queries
        CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
        CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
        """

        async with self.pool.acquire() as connection:
            await connection.execute(create_table_query)

    async def add_transaction(self, transaction: TransactionEntry) -> bool:
        """Add a transaction entry to PostgreSQL"""
        insert_query = """
        INSERT INTO transactions (
            transaction_date, transaction_detail, amount, currency, 
            category, service_subscription, receiver_name
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """

        try:
            async with self.pool.acquire() as connection:
                await connection.execute(
                    insert_query,
                    transaction.transaction_date,
                    transaction.transaction_detail,
                    transaction.amount,
                    transaction.currency,
                    transaction.category,
                    transaction.service_subscription,
                    transaction.receiver_name,
                )
            self.logger.info(
                f"Transaction added successfully: {transaction.transaction_detail}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to add transaction: {e}")
            return False

    async def get_transactions(
        self, limit: Optional[int] = None
    ) -> List[TransactionEntry]:
        """Retrieve transaction entries from PostgreSQL"""
        base_query = """
        SELECT transaction_date, transaction_detail, amount, currency, 
               category, service_subscription, receiver_name
        FROM transactions 
        ORDER BY transaction_date DESC
        """

        if limit:
            query = f"{base_query} LIMIT ${1}"
            params = (limit,)
        else:
            query = base_query
            params = ()

        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(query, *params)

                transactions = []
                for row in rows:
                    transaction = TransactionEntry(
                        transaction_date=row["transaction_date"],
                        transaction_detail=row["transaction_detail"],
                        amount=row["amount"],
                        currency=row["currency"],
                        category=row["category"],
                        service_subscription=row["service_subscription"],
                        receiver_name=row["receiver_name"],
                    )
                    transactions.append(transaction)

                return transactions

        except Exception as e:
            self.logger.error(f"Failed to retrieve transactions: {e}")
            return []

    async def close(self) -> None:
        """Close the PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("PostgreSQL connection pool closed")
