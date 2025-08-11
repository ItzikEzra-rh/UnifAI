from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from graph.state.graph_state import Channel
from graph.state.state_view import StateView
from elements.llms.common.chat.message import ChatMessage, Role
from core.iem.models import StandardEvents
from core.iem.payloads import TaskPayload
from typing import ClassVar
import uuid


class UserQuestionNode(IEMCapableMixin, BaseNode):
    """
    Workflow initiator that processes user input.
    
    Responsibilities:
    1. Convert user input to public conversation
    2. Broadcast processing events to adjacent nodes to start workflows
    3. Simple, focused - no message consumption needed
    """
    # Channel permissions
    READS: ClassVar[set[str]] = {Channel.USER_PROMPT}
    WRITES: ClassVar[set[str]] = {Channel.MESSAGES}

    def __init__(self,
                 *,
                 name: str = "user_question",
                 **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def run(self, state: StateView) -> StateView:
        prompt = state[Channel.USER_PROMPT]
        
        if not prompt or not prompt.strip():
            return state
        
        # 1. Promote to public conversation
        user_message = ChatMessage(role=Role.USER, content=prompt.strip())
        self.promote_to_messages(user_message)
        
        # 2. Notify adjacent nodes to start processing
        self._broadcast_user_query(prompt.strip())
        
        return state
    
    def _broadcast_user_query(self, user_query: str) -> None:
        """Broadcast user query to all adjacent nodes to start processing."""
        # Generate thread ID for this workflow
        thread_id = str(uuid.uuid4())
        
        # Create task payload
        payload_data = TaskPayload(
            result=user_query
        ).model_dump()
        
        # Broadcast to all adjacent nodes using built-in broadcaster
        self.messenger.broadcast_event(
            event_type=StandardEvents.PROCESSING_STARTED,
            data=payload_data,
            thread_id=thread_id
        )
