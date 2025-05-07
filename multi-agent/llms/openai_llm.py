from typing import Any, Dict, List, Optional, Iterator
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from llms.base_llm import BaseLLM, SupportsStreaming


class OpenAILLM(BaseLLM, SupportsStreaming):
    """
    LLM client for vLLM-served Qwen model using LangChain's ChatOpenAI wrapper.
    """

    def __init__(
            self,
            base_url: str = "http://0.0.0.0:8000/v1",
            model_name: str = "Qwen/Qwen1.5-7B-Chat",
            temperature: float = 0.7,
            max_tokens: int = 1024,
            api_key: str = "EMPTY",
            **extra: Any
    ):
        """
        :param base_url:     vLLM API base (OpenAI-compatible).
        :param model_name:   Qwen model ID (e.g. "Qwen/Qwen1.5-7B-Chat").
        :param temperature:  Sampling temperature.
        :param max_tokens:   Max tokens to generate.
        :param extra:        Extra kwargs passed to ChatOpenAI.
        """
        self._name = "vllm-qwen"
        self.client = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra
        )

    def chat(
            self,
            messages: List[Dict[str, Any]],
            *,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            stream: bool = False,
            **kwargs: Any
    ) -> str:
        """
        Send a chat request to the vLLM model.

        :param messages: List of {"role": "user"/"assistant"/"system", "content": "..."}
        """
        call_params: Dict[str, Any] = {}
        if temperature is not None:
            call_params["temperature"] = temperature
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens
        call_params.update(kwargs)

        # Convert to LangChain message objects
        lc_messages = self._to_lc_messages(messages)

        response = self.client.invoke(lc_messages, stream=stream, **call_params)
        return response.content

    def stream(
            self,
            messages: List[Dict[str, Any]],
            **call_params
    ) -> Iterator[str]:
        """
        Pass stream=True through to LangChain and unwrap content token by token.
        """
        lc_messages = self._to_lc_messages(messages)
        for chunk in self.client.stream(lc_messages, stream=True, **call_params):
            yield chunk.content

    @staticmethod
    def _to_lc_messages(messages):
        lc_msgs = []
        for m in messages:
            role, content = m["role"], m["content"]
            if role == "user":
                lc_msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_msgs.append(AIMessage(content=content))
            elif role == "system":
                lc_msgs.append(SystemMessage(content=content))
            else:
                raise ValueError(f"Unsupported role {role}")
        return lc_msgs

    @property
    def name(self) -> str:
        return self._name
