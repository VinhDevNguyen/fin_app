from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader, APIKey
from contextlib import asynccontextmanager
import os
import time
from typing import TypeVar, Generic, Optional, List, Dict
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from google import genai
from google.genai.types import HttpOptions
from .client.openai_client import OpenAIResponseClient
from .models.models import Response

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputRequest(BaseModel):
    system_prompt: str = Field(..., description="System prompt")
    chat_history: List[Dict] = Field(default=[], description="Chat history")
    user_prompt: str = Field(..., description="User prompt")
    mcp_servers: List[Dict] = Field(default=[{}], description="mcp_servers urls")


T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    timestamp: datetime
    status: int
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None


def create_response(
    data: Optional[T] = None,
    status_code: int = status.HTTP_200_OK,
    success: bool = True,
    message: Optional[str] = None,
) -> StandardResponse[T]:
    return StandardResponse(
        timestamp=datetime.now(timezone.utc),
        status=status_code,
        success=success,
        data=data,
        message=message,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for application startup and shutdown tasks. It initializes client for APIs within the application

    Args:
        app (FastAPI): The FastAPI app

    Yield:
        The state of the app so mapping_data and genai_client are always available

    """
    app.state.response_client = OpenAIResponseClient(
        os.environ.get("LLM_BASE_URL"),
        os.environ.get("LLM_API_KEY"),
        os.environ.get("LLM_MODEL"),
        os.environ.get("LLM_TEMPERATURE"),
    )
    logger.info("Initialized Response Client")
    try:
        yield
    finally:
        logger.info("Shutting down")


app = FastAPI(lifespan=lifespan, debug=True)


@app.post("/v1/get_response")
async def get_response(
    body: InputRequest,
):
    try:
        start = time.time()

        response = await app.state.response_client.get_response(
            body.system_prompt,
            body.chat_history,
            body.user_prompt,
            Response,
            body.mcp_servers,
        )

        logger.info(f"Processing time: {time.time() - start:.4f} second(s)")

        return create_response(response)
    except Exception as e:
        return create_response(data=[], status_code=500, success=False, message=str(e))
