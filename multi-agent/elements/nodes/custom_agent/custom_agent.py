from typing import Optional, Any, List
from graph.state.state_view import StateView
from elements.llms.common.chat.message import ChatMessage, Role
from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.capabilities.llm_capable import LlmCapableMixin
from elements.nodes.common.capabilities.retriever_capable import RetrieverCapableMixin
from elements.nodes.common.capabilities.tool_capable import ToolCapableMixin
from elements.nodes.common.models import AgentResult
from elements.providers.mcp_server_client.mcp_provider import McpProvider
from core.iem.packets import RequestPacket, EventPacket, ResponsePacket
from core.iem.models import StandardEvents, IEMError
from core.iem.payloads import TaskPayload


class CustomAgentNode(
    IEMCapableMixin,
    LlmCapableMixin,
    RetrieverCapableMixin,
    ToolCapableMixin,
    BaseNode
):
    """
    Generic agent that processes tasks using LLM + tools.
    
    Behavior:
    - Event → Process → Broadcast
    - Request → Process → Reply
    - Thread-scoped conversation memory
    """
    
    # No explicit READS/WRITES needed - purely message-driven via IEM

    def __init__(
            self,
            *,
            llm: Any,
            retriever: Any = None,
            tools: List[Any] = None,
            system_message: str = "",
            mcp_provider: McpProvider = None,
            max_rounds: Optional[int] = 15,
            **kwargs: Any
    ):
        super().__init__(
            llm=llm,
            retriever=retriever,
            tools=tools or [],
            system_message=system_message,
            **kwargs
        )
        self.mcp_provider = mcp_provider
        self.max_rounds = max_rounds

    def run(self, state: StateView) -> StateView:
        """Main entry point - process all incoming IEM messages."""
        # Initialize MCP tools if available
        if self.mcp_provider:
            # Add MCP tools to the internal tools dictionary
            for tool in self.mcp_provider.get_tools():
                self._tools[tool.name] = tool

        if self.tools:
            self._bind_tools(self.tools)

        # Process all messages
        self.process_messages(state)
        return state

    def handle_event(self, event: EventPacket) -> None:
        """Handle incoming events - process and broadcast."""
        # Extract task input
        task_input = event.data.get("result")
        if not task_input:
            return

        # Process the task
        result = self._process_task(task_input, thread_id=event.thread_id)

        # Always broadcast for events (for chaining)
        self.broadcast_event(
            StandardEvents.TASK_COMPLETE,
            TaskPayload(
                result=result.content,
                artifacts=result.artifacts,
                metrics=result.metrics
            ).model_dump(),
            thread_id=event.thread_id
        )

    def handle_request(self, request: RequestPacket) -> None:
        """Handle incoming requests - process and reply."""
        # Extract task input
        task_input = request.data.get("result")
        if not task_input:
            self.reply(request, error=IEMError(
                code="NO_INPUT",
                message="Missing result field"
            ))
            return

        # Process the task
        result = self._process_task(task_input, thread_id=request.thread_id)

        # Always reply for requests
        self.reply(
            request,
            result=TaskPayload(
                result=result.content,
                artifacts=result.artifacts,
                metrics=result.metrics
            ).model_dump()
        )

    def handle_response(self, response: ResponsePacket) -> None:
        """Handle incoming responses (optional - for agent coordination)."""
        pass

    def _process_task(self, input_text: str, thread_id: str = None) -> AgentResult:
        """
        Core processing logic - transforms input to output using LLM + tools.
        """
        # Build thread-scoped conversation history
        history = self._build_conversation_history(input_text, thread_id)

        # Execute LLM processing with optional tools
        if self.tools:
            assistant = self._execute_tool_cycle(
                initial_history=history,
                chat_function=self._chat,
                max_rounds=self.max_rounds
            )
        else:
            assistant = self._chat(history)

        # Ensure system message is persisted (only on first message)
        self._ensure_system_message_in_context(thread_id)
        
        # Store the NEW user input and assistant response in context
        self.add_to_chat_context(
            ChatMessage(role=Role.USER, content=input_text),
            thread_id=thread_id
        )
        self.add_to_chat_context(assistant, thread_id=thread_id)

        # Return structured result
        return AgentResult(
            content=assistant.content,
            artifacts={
                "thread_id": thread_id,
                "tool_calls": getattr(assistant, 'tool_calls', None)
            },
            metrics={
                "tokens_used": getattr(assistant, 'usage', {}),
                "tool_count": len(self.tools) if self.tools else 0
            }
        )

    def _build_conversation_history(
            self,
            input_text: str,
            thread_id: str = None
    ) -> List[ChatMessage]:
        """Build conversation history for LLM processing."""
        # Get thread-scoped history
        history = self.get_chat_context(thread_id=thread_id)

        # Add system message if configured
        if self.system_message:
            system_msg = ChatMessage(role=Role.SYSTEM, content=self.system_message)
            if not history or history[0].role != Role.SYSTEM:
                history.insert(0, system_msg)
            else:
                history[0] = system_msg

        # Create user message with current input
        user_msg = ChatMessage(role=Role.USER, content=input_text)

        # Apply retrieval augmentation if available
        if self.retriever:
            user_msg = self.augment_with_context(user_msg)

        history.append(user_msg)
        return history
    
    def _ensure_system_message_in_context(self, thread_id: str = None) -> None:
        """Ensure system message is stored in chat context if not already present."""
        if not self.system_message:
            return
            
        # Check if this thread already has messages (system message would be first)
        existing_context = self.get_chat_context(thread_id=thread_id)
        if not existing_context:
            # First message in this thread - store system message
            system_msg = ChatMessage(role=Role.SYSTEM, content=self.system_message)
            self.add_to_chat_context(system_msg, thread_id=thread_id)
