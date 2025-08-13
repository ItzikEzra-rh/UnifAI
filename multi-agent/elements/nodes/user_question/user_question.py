"""
User Question Node - Workflow Initiator

Converts user input into tasks and broadcasts to agent network.
Uses clean task-based architecture with agentic threading.
"""

from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.task import Task
from elements.nodes.common.agent_thread import AgentThread
from graph.state.graph_state import Channel
from graph.state.state_view import StateView
from elements.llms.common.chat.message import ChatMessage, Role
from typing import ClassVar


class UserQuestionNode(IEMCapableMixin, BaseNode):
    """
    Workflow initiator that processes user input.
    
    Clean, task-focused design:
    1. Convert user input to public conversation
    2. Create agentic task with proper threading
    3. Broadcast task to all adjacent nodes to start workflows
    """

    # Channel permissions - now includes task_threads
    READS: ClassVar[set[str]] = {Channel.USER_PROMPT, Channel.MESSAGES}
    WRITES: ClassVar[set[str]] = {Channel.MESSAGES, Channel.TASK_THREADS}

    def __init__(self, *, name: str = "user_question", **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def run(self, state: StateView) -> StateView:
        """Main execution - initiate workflow for user query."""
        prompt = state[Channel.USER_PROMPT]

        if not prompt or not prompt.strip():
            return state

        user_query = prompt.strip()

        # 1. Create and broadcast task to agent network with thread context
        self._initiate_workflow(user_query, state)

        # 2. Promote to public conversation
        user_message = ChatMessage(role=Role.USER, content=user_query)
        self.promote_to_messages(user_message)

        return state

    def _initiate_workflow(self, user_query: str, state: StateView) -> None:
        """
        Create agentic task and broadcast to start workflow.
        
        Creates proper thread ID, adds public messages to task_threads,
        and broadcasts task with thread context.
        """
        # Create thread ID for this workflow
        thread_id = AgentThread.create(
            initiator=self.get_context().uid,
            task_description="process_user_query"
        )

        # Get current public messages to establish thread context
        current_messages = state.get(Channel.MESSAGES, [])

        # Efficiently append public messages to task_threads for this thread
        if current_messages:
            # Get existing task_threads or create empty dict
            task_threads = state.get(Channel.TASK_THREADS, {})

            # Append to existing thread or create new one (pythonic way)
            task_threads.setdefault(thread_id, []).extend(current_messages)

            # Update state
            state[Channel.TASK_THREADS] = task_threads

        # Create clean, minimal task
        task = Task.create(
            content=user_query,
            should_respond=False,  # No direct response needed
            thread_id=thread_id,
            data={"role": Role.ASSISTANT}
        )

        # Broadcast to all adjacent nodes
        packet_ids = self.broadcast_task(task)

        # Optional: Log workflow initiation (for debugging)
        print(f"UserQuestion: Initiated workflow {thread_id} with {len(packet_ids)} agents")
        print(f"Thread context: {len(current_messages)} messages")
