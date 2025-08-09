from .base_database import DatabaseStrategy
from .postgres_database import PostgreSQLStrategy
from ..llm.pydantic_models.transactions import TransactionEntry
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Any
import asyncio

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop is running → safe to run normally
        return asyncio.run(coro)
    else:
        # A loop is already running → create a new task and wait for it
        return loop.create_task(coro)

class DatabaseManager:
    """Database manager that uses different strategies"""

    def __init__(self):
        self._strategy = None

    def set_strategy(self, strategy_name: str) -> None:
        """Change the database strategy"""
        strategies = {"postgres": PostgreSQLStrategy}
        try:
            strategy_class = strategies[strategy_name]
            self._strategy = strategy_class()
            logging.info(f"Database strategy set to: {strategy_name}")
        except KeyError:
            raise ValueError(f"Unknown database strategy: {strategy_name}")

    async def initialize(self) -> None:
        """Initialize the current strategy"""
        await self._strategy.initialize()
        
    def add_transaction_sync(self, transaction: TransactionEntry) -> bool:
        from .base_database import DatabaseStrategy
from .postgres_database import PostgreSQLStrategy
from ..llm.pydantic_models.transactions import TransactionEntry
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Any
import asyncio
import threading
import concurrent.futures
import sys

class DatabaseManager:
    """Database manager that uses different strategies"""

    def __init__(self):
        self._strategy = None

    def set_strategy(self, strategy_name: str, connection_string: str) -> None:
        """Change the database strategy"""
        strategies = {"postgres": PostgreSQLStrategy}
        try:
            strategy_class = strategies[strategy_name]
            self._strategy = strategy_class(connection_string = connection_string)
            logging.info(f"Database strategy set to: {strategy_name}")
        except KeyError:
            raise ValueError(f"Unknown database strategy: {strategy_name}")

    async def initialize(self) -> None:
        """Initialize the current strategy"""
        await self._strategy.initialize()
        
    def add_transaction_sync(self, transaction: TransactionEntry) -> bool:
        """
        BULLETPROOF sync wrapper that handles ALL edge cases.
        This WILL work regardless of event loop state.
        """
        logging.info("Starting sync transaction add")
        
        def _run_async_in_thread():
            """Run the async code in a completely fresh thread with new event loop"""
            # Create completely new event loop in this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            
            try:
                # Initialize strategy if needed (in the new loop)
                if self._strategy is None:
                    raise ValueError("Database strategy not set")
                
                # Run the async initialization and transaction in the new loop
                async def _do_work():
                    await self.initialize()
                    result = await self.add_transaction(transaction)
                    await self.close()
                    return result
                
                return new_loop.run_until_complete(_do_work())
                
            except Exception as e:
                logging.error(f"Error in async thread: {e}")
                raise
            finally:
                # Ensure cleanup
                try:
                    new_loop.close()
                except Exception as e:
                    logging.warning(f"Error closing loop: {e}")

        # Always use thread-based approach - it's the only reliable way
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_async_in_thread)
            try:
                result = future.result(timeout=30)  # 30 second timeout
                logging.info("Sync transaction completed successfully")
                return result
            except concurrent.futures.TimeoutError:
                logging.error("Transaction timed out after 30 seconds")
                raise
            except Exception as e:
                logging.error(f"Transaction failed: {e}")
                raise


    async def add_transaction(self, transaction: TransactionEntry) -> bool:
        """Add transaction using current strategy"""
        return await self._strategy.add_transaction(transaction)

    async def get_transactions(
        self, limit: Optional[int] = None
    ) -> List[TransactionEntry]:
        """Get transactions using current strategy"""
        return await self._strategy.get_transactions(limit)

    async def close(self) -> None:
        """Close connections using current strategy"""
        await self._strategy.close()

    @asynccontextmanager
    async def managed_connection(self):
        """Context manager for automatic cleanup"""
        try:
            await self.initialize()
            yield self
        finally:
            await self.close()
