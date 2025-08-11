from typing import List, Dict, Any
from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.capabilities.llm_capable import LlmCapableMixin
from elements.nodes.common.models import AgentResult
from graph.state.graph_state import Channel
from graph.state.state_view import StateView
from elements.llms.common.chat.message import ChatMessage, Role
from core.iem.packets import EventPacket, RequestPacket, ResponsePacket
from core.iem.models import StandardEvents, IEMError
from core.iem.payloads import TaskPayload


class LLMMergerNode(IEMCapableMixin, LlmCapableMixin, BaseNode):
    """
    Uses an LLM to intelligently merge outputs from multiple agents.
    
    Behavior:
    - Events: Collects results and merges them, then broadcasts
    - Requests: Merges provided inputs and replies with merged result
    - Uses LLM to create coherent, unified responses from multiple inputs
    """
    
    READS = set()
    WRITES = set()

    def __init__(
        self,
        *,
        llm: Any,
        system_message: str = "You are a skilled editor. Merge the following responses into a single, coherent, and comprehensive answer. Remove redundancy while preserving all important information.",
        merge_prompt_template: str = "Please merge these responses into a single comprehensive answer:\n\n{inputs}\n\nProvide a unified, well-structured response:",
        **kwargs
    ):
        super().__init__(llm=llm, system_message=system_message, **kwargs)
        self.merge_prompt_template = merge_prompt_template
        self._collected_results: Dict[str, List[str]] = {}  # thread_id -> results

    def run(self, state: StateView) -> StateView:
        """Process incoming IEM messages, then merge all collected events."""
        # First, process all incoming messages (collect phase)
        self.process_messages(state)
        
        # Then, merge all collected events for each thread
        self._merge_all_collected_events()
        
        return state

    def handle_event(self, event: EventPacket) -> None:
        """Collect event results - merging happens after all events are processed."""
        result = event.data.get("result")
        if not result:
            return
        
        thread_id = event.thread_id or "default"
        
        # Just collect - no immediate merging
        if thread_id not in self._collected_results:
            self._collected_results[thread_id] = []
        
        self._collected_results[thread_id].append(result)

    def handle_request(self, request: RequestPacket) -> None:
        """Merge provided inputs and reply (doesn't use collected events)."""
        pass

    def handle_response(self, response: ResponsePacket) -> None:
        """Handle responses (not typically used by merger)."""
        pass

    def _merge_all_collected_events(self) -> None:
        """Merge all collected events for each thread and broadcast results."""
        threads_to_merge = list(self._collected_results.keys())
        
        for thread_id in threads_to_merge:
            results = self._collected_results.get(thread_id, [])
            if results:  # Only merge if there are results
                self._merge_and_broadcast(thread_id)

    def _merge_and_broadcast(self, thread_id: str) -> None:
        """Merge collected results and broadcast the unified result."""
        results = self._collected_results.get(thread_id, [])
        if not results:
            return
        
        try:
            # Merge using LLM
            merged_result = self._merge_inputs(results, thread_id)
            
            # Broadcast merged result
            self.broadcast_event(
                StandardEvents.TASK_COMPLETE,
                TaskPayload(
                    result=merged_result.content,
                    artifacts=merged_result.artifacts,
                    metrics=merged_result.metrics
                ).model_dump(),
                thread_id=thread_id
            )
            
            # Clean up
            self._collected_results.pop(thread_id, None)
            
        except Exception as e:
            # Log error but don't crash
            print(f"Error merging results: {e}")

    def _merge_inputs(self, inputs: List[str], thread_id: str = None) -> AgentResult:
        """Use LLM to merge multiple inputs into a coherent response."""
        if not inputs:
            raise ValueError("No inputs to merge")
        
        if len(inputs) == 1:
            # Single input - no merging needed
            return AgentResult(
                content=inputs[0],
                artifacts={"input_count": 1},
                metrics={"merged": False}
            )
        
        # Format inputs for merging
        formatted_inputs = []
        for i, inp in enumerate(inputs, 1):
            formatted_inputs.append(f"**Response {i}:**\n{inp}")
        
        inputs_text = "\n\n".join(formatted_inputs)
        merge_prompt = self.merge_prompt_template.format(inputs=inputs_text)
        
        # Build conversation for LLM
        history = self.get_chat_context(thread_id=thread_id)
        
        # Add system message if not already present
        if self.system_message:
            system_msg = ChatMessage(role=Role.SYSTEM, content=self.system_message)
            if not history or history[0].role != Role.SYSTEM:
                history.insert(0, system_msg)
            else:
                history[0] = system_msg
        
        # Add merge request
        user_msg = ChatMessage(role=Role.USER, content=merge_prompt)
        history.append(user_msg)
        
        # Get merged response from LLM
        assistant = self._chat(history)
        
        # Update thread context
        self.add_to_chat_context(user_msg, thread_id=thread_id)
        self.add_to_chat_context(assistant, thread_id=thread_id)
        
        return AgentResult(
            content=assistant.content,
            artifacts={
                "input_count": len(inputs),
                "original_inputs": inputs,
                "thread_id": thread_id
            },
            metrics={
                "merged": True,
                "input_length": sum(len(inp) for inp in inputs),
                "output_length": len(assistant.content)
            }
        )