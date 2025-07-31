import logging
from functools import wraps
from typing import Any, Callable, Optional

from langfuse import Langfuse, observe

logger = logging.getLogger(__name__)


class LangfuseWrapper:
    """Wrapper for Langfuse integration."""

    _instance: Optional[Langfuse] = None
    _initialized: bool = False

    @classmethod
    def initialize(
        cls,
        secret_key: Optional[str] = None,
        public_key: Optional[str] = None,
        host: Optional[str] = None,
    ) -> None:
        """Initialize Langfuse client if credentials are provided."""
        if secret_key and public_key:
            try:
                cls._instance = Langfuse(
                    secret_key=secret_key,
                    public_key=public_key,
                    host=host or "https://cloud.langfuse.com",
                )
                cls._initialized = True
                logger.info("Langfuse initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                cls._initialized = False
        else:
            logger.info("Langfuse credentials not provided, skipping initialization")
            cls._initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Langfuse is initialized."""
        return cls._initialized

    @classmethod
    def get_instance(cls) -> Optional[Langfuse]:
        """Get Langfuse instance."""
        return cls._instance if cls._initialized else None

    @classmethod
    def trace_llm_call(
        cls, name: str, metadata: Optional[dict[str, Any]] = None
    ) -> Callable:
        """Decorator to trace LLM calls with Langfuse."""

        def decorator(func: Callable) -> Callable:
            if not cls._initialized:
                return func

            @wraps(func)
            @observe(name=name, capture_input=True, capture_output=True)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if metadata and cls._instance:
                    cls._instance.update_current_trace(metadata=metadata)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def flush(cls) -> None:
        """Flush Langfuse client."""
        if cls._instance:
            cls._instance.flush()
