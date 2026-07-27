"""Agent loop for executing agent runs."""

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import AgentTools, ToolResult
from app.llm.client import LLMClient, Message, Tool
from app.models.agent import AgentRun, AgentRunKind


class AgentLoop:
    """Agent loop for executing agent runs."""

    def __init__(
        self,
        session: AsyncSession,
        run_id: str,
        kind: AgentRunKind,
        model: str = "nousresearch/hermes-4-405b",
    ):
        """Initialize the agent loop.

        Args:
            session: Database session
            run_id: Agent run ID
            kind: Agent run kind
            model: Model name
        """
        self.session = session
        self.run_id = run_id
        self.kind = kind
        self.model = model
        self.llm = LLMClient(model=model)
        self.tools = AgentTools(session=session)
        self.transcript: List[Dict[str, Any]] = []
        self.tokens_in = 0
        self.tokens_out = 0

    async def run(
        self,
        system_prompt: str,
        user_message: str,
        max_iterations: int = 12,
    ) -> Dict[str, Any]:
        """Run the agent loop.

        Args:
            system_prompt: System prompt
            user_message: User message
            max_iterations: Maximum iterations

        Returns:
            Result dictionary
        """
        # Initialize messages
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_message),
        ]

        # Get tools for this agent kind
        tools = self._get_tools()

        # Run loop
        for iteration in range(max_iterations):
            # Call LLM
            response = await self.llm.chat(messages, tools)

            # Update token counts
            self.tokens_in += response.tokens_in
            self.tokens_out += response.tokens_out

            # Add assistant message to transcript
            self.transcript.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {"name": tc.name, "arguments": tc.content}
                        for tc in response.tool_calls
                    ],
                }
            )

            # If no tool calls, we're done
            if not response.tool_calls:
                break

            # Execute tool calls
            for tool_call in response.tool_calls:
                result = await self._execute_tool(tool_call)

                # Add tool result to transcript
                self.transcript.append(
                    {
                        "role": "tool",
                        "name": tool_call.name,
                        "content": result.content,
                    }
                )

                # Add tool result to messages
                messages.append(
                    Message(
                        role="tool",
                        content=result.content,
                        name=tool_call.name,
                    )
                )

        # Update agent run
        await self._update_run(
            {
                "status": "completed",
                "output": {
                    "content": response.content,
                    "tool_calls": [
                        {"name": tc.name, "arguments": tc.content}
                        for tc in response.tool_calls
                    ],
                },
                "transcript": self.transcript,
                "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out,
                "finished_at": datetime.utcnow(),
            }
        )

        return {
            "content": response.content,
            "tool_calls": [
                {"name": tc.name, "arguments": tc.content} for tc in response.tool_calls
            ],
        }

    def _get_tools(self) -> List[Tool]:
        """Get tools for this agent kind."""
        tools = []

        if self.kind == AgentRunKind.CAMPAIGN_PLANNER:
            tools = [
                Tool(
                    name="search_contacts",
                    description="Search contacts by stage and text",
                    parameters={
                        "type": "object",
                        "properties": {
                            "stage": {"type": "string"},
                            "text": {"type": "string"},
                            "limit": {"type": "integer"},
                        },
                    },
                ),
                Tool(
                    name="create_campaign",
                    description="Create a new campaign",
                    parameters={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "goal": {"type": "string"},
                            "campaign_type": {"type": "string"},
                            "segment_id": {"type": "string"},
                        },
                    },
                ),
                Tool(
                    name="create_template",
                    description="Create a template for a campaign",
                    parameters={
                        "type": "object",
                        "properties": {
                            "campaign_id": {"type": "string"},
                            "subject": {"type": "string"},
                            "body_markdown": {"type": "string"},
                            "variant_label": {"type": "string"},
                        },
                    },
                ),
            ]
        elif self.kind == AgentRunKind.COPYWRITER:
            tools = [
                Tool(
                    name="generate_copy",
                    description="Generate email copy using LLM",
                    parameters={
                        "type": "object",
                        "properties": {
                            "goal": {"type": "string"},
                            "audience": {"type": "object"},
                            "tone": {"type": "string"},
                        },
                    },
                ),
            ]
        elif self.kind == AgentRunKind.INBOX:
            tools = [
                Tool(
                    name="analyze_reply",
                    description="Analyze a reply and suggest response",
                    parameters={
                        "type": "object",
                        "properties": {
                            "reply_text": {"type": "string"},
                            "context": {"type": "object"},
                        },
                    },
                ),
            ]
        elif self.kind == AgentRunKind.OPTIMIZER:
            tools = [
                Tool(
                    name="get_campaign_metrics",
                    description="Get campaign metrics",
                    parameters={
                        "type": "object",
                        "properties": {
                            "campaign_id": {"type": "string"},
                        },
                    },
                ),
            ]

        return tools

    async def _execute_tool(self, tool_call: Dict[str, Any]) -> ToolResult:
        """Execute a tool call."""
        tool_name = tool_call.name
        tool_args = tool_call.arguments

        try:
            if tool_name == "search_contacts":
                result = await self.tools.search_contacts(**tool_args)
                return ToolResult(
                    success=True,
                    content=str(result),
                )
            elif tool_name == "create_campaign":
                result = await self.tools.create_campaign(**tool_args)
                return ToolResult(
                    success=True,
                    content=str(result),
                )
            elif tool_name == "create_template":
                result = await self.tools.create_template(**tool_args)
                return ToolResult(
                    success=True,
                    content=str(result),
                )
            elif tool_name == "generate_copy":
                result = await self.tools.generate_copy(**tool_args)
                return ToolResult(
                    success=True,
                    content=str(result),
                )
            elif tool_name == "analyze_reply":
                result = await self.tools.analyze_reply(**tool_args)
                return ToolResult(
                    success=True,
                    content=str(result),
                )
            elif tool_name == "get_campaign_metrics":
                result = await self.tools.get_campaign_metrics(**tool_args)
                return ToolResult(
                    success=True,
                    content=str(result),
                )
            else:
                return ToolResult(
                    success=False,
                    content=f"Unknown tool: {tool_name}",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                content=f"Error executing tool {tool_name}: {str(e)}",
            )

    async def _update_run(self, updates: Dict[str, Any]) -> None:
        """Update the agent run in the database."""
        result = await self.session.execute(
            select(AgentRun).where(AgentRun.id == self.run_id)
        )
        run = result.scalar_one_or_none()

        if run:
            for key, value in updates.items():
                setattr(run, key, value)
            await self.session.commit()


async def run_agent(
    session: AsyncSession,
    run_id: str,
    kind: AgentRunKind,
    system_prompt: str,
    user_message: str,
    model: str = "nousresearch/hermes-4-405b",
) -> Dict[str, Any]:
    """Run an agent.

    Args:
        session: Database session
        run_id: Agent run ID
        kind: Agent run kind
        system_prompt: System prompt
        user_message: User message
        model: Model name

    Returns:
        Result dictionary
    """
    loop = AgentLoop(session, run_id, kind, model)
    return await loop.run(system_prompt, user_message)
