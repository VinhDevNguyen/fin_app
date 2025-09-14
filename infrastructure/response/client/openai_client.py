import logging
from typing import Any, List, Dict, Literal
from pydantic import BaseModel
from contextlib import AsyncExitStack

from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.mcp import (
    MCPServerSse,
    MCPServerSseParams,
)
from .base import ResponseClient

logger = logging.getLogger(__name__)


class OpenAIResponseClient(ResponseClient):
    """Client for OpenAI format"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ):
        super().__init__()
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.completion_model = OpenAIChatCompletionsModel(
            model=self.model, openai_client=self.client
        )
        self.temperature = temperature
        self.provider_name = "openai"
        logger.info(f"Initialized OpenAI Response client with model: {model}")

    async def create_chat_prompts(
        self, system_prompt: str, chat_history: List[Dict[str, str]], user_prompt: str
    ) -> Dict[str, Any]:
        """Create chat prompts based on system instruction, history, and latest user message.

        Args:
            system_prompt (str): The system-level instruction for the chat.
            chat_history (List[Dict[str, str]]): A list of past messages, where each message
                is a dict with keys 'role' ('user' or 'assistant') and 'content'.
                This should always be an even-length list (pairs of user/assistant).
            user_prompt (str): The latest user message to append.

        Returns:
            Dict[str, Any]: A dict containing a 'messages' key that holds
            the formatted conversation history including the system prompt.
        """

        # Validate history alternates correctly
        for i, msg in enumerate(chat_history):
            if msg["role"] not in {"user", "assistant"}:
                raise ValueError(f"Invalid role at index {i}: {msg['role']}")

        messages = []  # [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_prompt})

        return {"messages": messages}

    async def format_mcp(self, server_url: str, server_label: str):
        return {
            "type": "mcp",
            "server_label": server_label,
            "server_url": f"{server_url}/mcp",
            "require_approval": "never",
        }

    async def get_response(
        self,
        system_prompt: str,
        chat_history: List[Dict],
        user_prompt: str,
        output_format: BaseModel,
        mcp_servers=[],
    ):

        try:
            input = await self.create_chat_prompts(
                system_prompt, chat_history, user_prompt
            )

            async with AsyncExitStack() as stack:
                servers = [MCPServerSse(params=MCPServerSseParams(url=mcp_server["url"])) for mcp_server in mcp_servers]

                live_servers = [await stack.enter_async_context(server) for server in servers]

                agent = Agent(
                    name="base_agent",
                    instructions=system_prompt,
                    model=self.completion_model,
                    mcp_servers=live_servers,
                )

            response = await Runner.run(starting_agent=agent, input=input["messages"])

            return {"response": response.final_output}
        # tools = []

        # for mcp_server in mcp_servers:
        #     tools.append(await self.format_mcp(mcp_server["url"], mcp_server["label"]))

        # try:
        #     response = await self.client.chat.completions.parse(
        #         model=self.model,
        #         messages=input["messages"],
        #         temperature=self.temperature,
        #         response_format=output_format,
        #         tool_choice="auto" if tools else "none",
        #         tools=tools,
        #     )

        #     result = response.choices[0].message.parsed
        #     if isinstance(result, output_format):
        #         return result
        #     else:
        #         logger.error(f"OpenAI failed to produce correct output")
        #         raise

        except Exception as e:
            logger.error(f"Error getting response from OpenAI: {str(e)}")
            raise
