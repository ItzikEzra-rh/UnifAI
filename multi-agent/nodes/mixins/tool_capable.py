import asyncio
from typing import Iterable, Any, Dict, List
from llms.chat.message import ChatMessage, ToolCall, Role
from tools.base_tool import BaseTool


class ToolCapableMixin:
    """Mixin to run tool_calls asynchronously under the hood,
    while exposing a sync `invoke_tools()` API."""

    def __init__(self, *, tools: List[BaseTool], **kwargs: Any):
        super().__init__(**kwargs)
        self.tools: List[BaseTool] = tools
        # map name → tool instance
        self._tool_map: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

    def invoke_tools(self, msg: ChatMessage) -> List[ChatMessage]:
        """Sync entry point. Runs the async tool invocation and waits for results."""
        if msg.role != Role.ASSISTANT or not msg.tool_calls:
            return []

        # run the async inner function on whatever event loop context we have
        return self._run_async(self._ainvoke_tools(msg))

    async def _ainvoke_tools(self, msg: ChatMessage) -> List[ChatMessage]:
        """Async core: invoke each tool in parallel via tool.arun()."""

        async def _call(tc: ToolCall) -> ChatMessage:
            tool = self._tool_map.get(tc.name)
            if not tool:
                raise ValueError(f"No tool registered under name '{tc.name}'")

            # validate args if schema provided
            kwargs = tc.args
            if tool.args_schema:
                kwargs = tool.args_schema(**kwargs).dict()

            result = await tool.arun(**kwargs)
            return ChatMessage(
                role=Role.TOOL,
                content=str(result),
                tool_call_id=tc.tool_call_id
            )

        return list(await asyncio.gather(*(_call(tc) for tc in msg.tool_calls)))

    @staticmethod
    def _run_async(awaitable: Any) -> Any:
        """
        Run an awaitable from sync code.
        - If no loop is running, uses asyncio.run().
        - If already inside a loop, uses run_until_complete().
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # no loop: safe to start a new one
            return asyncio.run(awaitable)
        else:
            # loop already running (e.g. in a web framework), so block on it
            return loop.run_until_complete(awaitable)
