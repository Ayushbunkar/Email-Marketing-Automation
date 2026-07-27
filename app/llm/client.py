"""LLM client for Hermes LLM API."""

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class Message:
    """LLM message."""

    role: str
    content: str


@dataclass
class Tool:
    """LLM tool definition."""

    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class ToolResult:
    """LLM tool result."""

    name: str
    content: str


@dataclass
class ChatResponse:
    """LLM chat response."""

    content: str
    tool_calls: List[ToolResult]
    model: str
    tokens_in: int
    tokens_out: int


class LLMClient:
    """Client for Hermes LLM API."""

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        model: str = None,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the LLM client."""
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("PLANNER_MODEL", "nousresearch/hermes-4-405b")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        max_iterations: int = 12,
    ) -> ChatResponse:
        """Send a chat request to the LLM with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": m.role, "content": m.content} for m in messages
                    ],
                }

                if tools:
                    payload["tools"] = [
                        {
                            "type": "function",
                            "function": {
                                "name": t.name,
                                "description": t.description,
                                "parameters": t.parameters,
                            },
                        }
                        for t in tools
                    ]

                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()

                data = response.json()
                choice = data["choices"][0]
                message = choice["message"]

                # Parse tool calls
                tool_calls = []
                if "tool_calls" in message:
                    for tc in message["tool_calls"]:
                        tool_calls.append(
                            ToolResult(
                                name=tc["function"]["name"],
                                content=tc["function"]["arguments"],
                            )
                        )

                return ChatResponse(
                    content=message.get("content", ""),
                    tool_calls=tool_calls,
                    model=self.model,
                    tokens_in=data["usage"]["prompt_tokens"],
                    tokens_out=data["usage"]["completion_tokens"],
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500:
                    # Retry on server errors
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2**attempt))
                        continue
                raise

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    continue
                raise

        raise last_error

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
