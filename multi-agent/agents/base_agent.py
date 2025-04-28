# agents/base_agent.py

"""
agents/base_agent.py

Defines the BaseAgent abstract class using the Template Method pattern.
Subclasses override specific steps of the answer-generation pipeline,
while BaseAgent manages the overall algorithm.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAgent(ABC):
    """
    Abstract base for all Agents, encapsulating:
      1) Retrieving context (RAG)
      2) Building prompt/messages
      3) Invoking the LLM (with optional tools)
      4) Post-processing the LLM output

    Implements the Template Method pattern: subclasses override
    protected methods (_retrieve, _build_messages, _call_llm, _post_process)
    to customize behavior without changing the overall algorithm.
    """

    def __init__(
            self,
            name: str,
            system_message: str,
            llm: Any,
            retriever: Optional[Any] = None,
            tools: Optional[List[Any]] = None,
            retries: int = 1,
    ):
        """
        :param name: Unique identifier for logging and state keys.
        :param system_message: The top-level system prompt for the LLM.
        :param llm: An LLM client supporting .chat(messages, tools) -> str
        :param retriever: Optional retriever supporting .retrieve(query) -> List[str]
        :param tools: Optional list of tool adapters for LLM tool use.
        :param retries: Number of attempts for _call_llm on failure.
        """
        self.name = name
        self.system_message = system_message
        self.llm = llm
        self.retriever = retriever
        self.tools = tools or []
        self.retries = max(1, retries)

    def get_answer(self, query: str, *, state: Optional[Dict[str, Any]] = None) -> str:
        """
        The public entry point for generating an answer.
        Follows the Template Method steps:
          1) Retrieve context
          2) Build chat messages
          3) Call the LLM
          4) Post-process the LLM response
        """
        # 1) Retrieve RAG context if available
        context = self._retrieve(query, state)

        # 2) Build the sequence of messages/prompts
        messages = self._build_messages(query, context, state)

        # 3) Invoke the LLM (with retry logic)
        raw_response = self._call_llm(messages, state)

        # 4) Apply any post-processing (cleanup, parsing)
        answer = self._post_process(raw_response, state)
        return answer

    def _retrieve(self, query: str, state: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Default retrieval: call self.retriever.retrieve(query) if present,
        otherwise return an empty list.
        """
        if self.retriever:
            return self.retriever.retrieve(query)
        return []

    def _build_messages(
            self,
            query: str,
            context: List[str],
            state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Construct the chat message list for the LLM.
        Default:
          - system_message as first message
          - context chunks as a system message
          - user query as the final user message
        """
        msgs = [{"role": "system", "content": self.system_message}]
        if context:
            joined = "\n\n".join(context)
            msgs.append({"role": "system", "content": f"Context:\n{joined}"})
        msgs.append({"role": "user", "content": query})
        return msgs

    def _call_llm(
            self,
            messages: List[Dict[str, str]],
            state: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Invoke the LLM with the prepared messages and tools.
        Retries up to self.retries on exception.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                return self.llm.chat(messages=messages, tools=self.tools)
            except Exception as exc:
                last_exc = exc
        # If we exhaust retries, propagate the last exception
        raise RuntimeError(f"Agent '{self.name}' LLM call failed after {self.retries} attempts") from last_exc

    def _post_process(self, raw: str, state: Optional[Dict[str, Any]] = None) -> str:
        """
        Hook for subclasses to clean up or parse the raw LLM output.
        Default: identity.
        """
        return raw
