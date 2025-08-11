from typing import List
from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from graph.state.graph_state import Channel
from graph.state.state_view import StateView
from elements.llms.common.chat.message import ChatMessage, Role
from core.iem.packets import EventPacket, RequestPacket, ResponsePacket


class FinalAnswerNode(IEMCapableMixin, BaseNode):
    """
    Simple final node that collects all incoming events and merges them into a final message.
    
    Behavior:
    - Receives any events from agents
    - Collects all results
    - Merges them into one final message
    - Promotes to public conversation
    """
    
    READS = {Channel.MESSAGES}
    WRITES = {Channel.MESSAGES, Channel.OUTPUT}

    def __init__(self, *, name: str = "final_answer", **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self._collected_results: List[str] = []

    def run(self, state: StateView) -> StateView:
        """Process all incoming events and create final answer."""
        # Process all incoming messages
        self.process_messages(state)
        
        # Create final answer if we have collected results
        if self._collected_results:
            final_answer = self._merge_results()
            self.promote_to_messages(final_answer)
            state[Channel.OUTPUT] = final_answer
            
            # Clear collected results
            self._collected_results.clear()
        
        return state

    def handle_event(self, event: EventPacket) -> None:
        """Collect any event result."""
        result = event.data.get("result")
        if result and result.strip():
            self._collected_results.append(result.strip())

    def handle_request(self, request: RequestPacket) -> None:
        """Ignore requests - final node doesn't handle requests."""
        pass

    def handle_response(self, response: ResponsePacket) -> None:
        """Ignore responses."""
        pass

    def _merge_results(self) -> str:
        """Merge all collected results into one final message."""
        if not self._collected_results:
            return "I apologize, but I don't have any information to provide."
        
        if len(self._collected_results) == 1:
            return self._collected_results[0]
        
        # Remove duplicates while preserving order
        unique_results = []
        seen = set()
        for result in self._collected_results:
            if result not in seen:
                unique_results.append(result)
                seen.add(result)
        
        if len(unique_results) == 1:
            return unique_results[0]
        
        # Join multiple results
        return "\n\n".join(unique_results)