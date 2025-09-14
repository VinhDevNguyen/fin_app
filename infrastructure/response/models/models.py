from pydantic import BaseModel, Field
from typing import Any, List, Dict, Literal


class Response(BaseModel):
    response: str = Field(..., description="The output response of the LLM")
    