from typing import Optional, Any, List, ClassVar
from copy import deepcopy
from graph.state.state_view import StateView
from graph.state.graph_state import Channel
from elements.llms.common.chat.message import ChatMessage, Role
from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.capabilities.llm_capable import LlmCapableMixin
from elements.nodes.common.capabilities.retriever_capable import RetrieverCapableMixin
from elements.nodes.common.capabilities.tool_capable import ToolCapableMixin
from elements.nodes.common.task import Task
from elements.providers.mcp_server_client.mcp_provider import McpProvider


class CustomAgentNode(
    IEMCapableMixin,
    LlmCapableMixin,
    RetrieverCapableMixin,
    ToolCapableMixin,
    BaseNode
):
    """
    Generic agent that processes tasks using LLM + tools.
    
    Clean task-based behavior:
    - Processes TaskPackets via handle_task_packet()
    - Uses task_threads for conversation context
    - Intelligent response handling based on task.should_respond
    """

    # Channel permissions - reads and writes to task_threads for conversation context
    READS: ClassVar[set[str]] = {Channel.TASK_THREADS}
    WRITES: ClassVar[set[str]] = {Channel.TASK_THREADS}

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
        """Main entry point - process all incoming TaskPackets."""
        # Initialize MCP tools if available
        if self.mcp_provider:
            # Add MCP tools to the internal tools dictionary
            for tool in self.mcp_provider.get_tools():
                self._tools[tool.name] = tool

        if self.tools:
            self._bind_tools(self.tools)

        # Process all incoming packets
        self.process_packets(state)
        return state

    def handle_task_packet(self, packet) -> None:
        """
        Handle incoming task packets.
        
        Core logic:
        1. Extract task from packet
        2. Get thread conversation from task_threads
        3. Build conversation history with task
        4. Process with LLM + tools
        5. Create response task and send appropriately
        """
        try:
            # 1. Extract task from packet
            task = packet.extract_task()

            # 2. Get current state to access task_threads
            state = self.get_state()

            # 3. Process the task
            assistant_response = self._process_task_with_thread_context(task, state)

            # 4. Update task content to the thread
            self._update_task_thread(task, state)

            # 5. Handle response based on task requirements
            self._handle_task_response(task, assistant_response, packet)

        except Exception as e:
            print(f"CustomAgent: Error processing task: {e}")
            # Could send error response if needed

    def _process_task_with_thread_context(
            self,
            task: Task,
            state: StateView
    ) -> ChatMessage:
        """
        Process task using thread context from task_threads.
        
        Builds conversation history from task_threads, adds system message,
        appends current task, processes with LLM + tools.
        """
        # Get thread conversation from task_threads (deep copy to avoid mutation)
        thread_conversations = state.get(Channel.TASK_THREADS, {})
        thread_history = thread_conversations.get(task.thread_id, [])
        conversation_history = deepcopy(thread_history)  # Don't modify original

        # Add system message at the start if configured
        if self.system_message:
            system_msg = ChatMessage(role=Role.SYSTEM, content=self.system_message)
            if not conversation_history or conversation_history[0].role != Role.SYSTEM:
                conversation_history.insert(0, system_msg)
            else:
                conversation_history[0] = system_msg

        # Add current task as user message at the end
        user_msg = ChatMessage(role=Role.USER, content=task.content)

        # Apply retrieval augmentation if available
        if self.retriever:
            user_msg = self.augment_with_context(user_msg)

        conversation_history.append(user_msg)

        # Execute LLM processing with optional tools
        if self.tools:
            assistant = self._execute_tool_cycle(
                initial_history=conversation_history,
                chat_function=self._chat,
                max_rounds=self.max_rounds
            )
        else:
            assistant = self._chat(conversation_history)

        return assistant

    def _update_task_thread(
            self,
            task: Task,
            state: StateView
    ) -> None:
        """
        Update task_threads with the task content
        """
        # Get current task_threads
        task_threads = state.get(Channel.TASK_THREADS, {})

        # append task content to the thread
        if task.thread_id in task_threads:
            role = task.data.get("role", Role.ASSISTANT)
            task_threads[task.thread_id].append(ChatMessage(role=role, content=task.content))

    def _handle_task_response(
            self,
            original_task: Task,
            assistant_response: ChatMessage,
            original_packet
    ) -> None:
        """
        Handle response based on task.should_respond.
        
        Logic:
        - Add user task and assistant response to task_threads
        - If should_respond=True: Create response task with correlation_task_id
        - If should_respond=False: Create new task and broadcast
        """
        if original_task.should_respond:
            # Create response task
            response_task = Task.respond_success(
                original_task=original_task,
                result={"content": assistant_response.content}
            )

            # Reply to original sender
            self.reply_task(original_packet, response_task)

        else:
            # Create new task with same thread context
            new_task = Task.create(
                content=assistant_response.content,
                should_respond=False,
                thread_id=original_task.thread_id
            )

            # Broadcast to adjacent nodes
            self.broadcast_task(new_task)
