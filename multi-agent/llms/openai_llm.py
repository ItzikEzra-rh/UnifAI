from typing import Any, Dict, List, Optional, Iterator
from langchain_openai import ChatOpenAI
from llms.base_llm import BaseLLM
from core.contracts import SupportsStreaming
from llms.chat.converter import LangChainConverter
from llms.chat.message import ChatMessage
from tools.base_tool import BaseTool
from tools.converter import LangChainToolsConverter


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
            messages: List[ChatMessage],
            *,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            stream: bool = False,
            **kwargs: Any
    ) -> ChatMessage:
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
        lc_messages = LangChainConverter.to_lc(messages)

        response = self.client.invoke(lc_messages, stream=stream, **call_params)
        return LangChainConverter.from_lc_message(response)

    def stream(
            self,
            messages: List[ChatMessage],
            **call_params
    ) -> Iterator[str]:
        """
        Pass stream=True through to LangChain and unwrap content token by token.
        """
        lc_messages = LangChainConverter.to_lc(messages)
        for chunk in self.client.stream(lc_messages, stream=True, **call_params):
            yield chunk.content

    def bind_tools(self, tools: List[BaseTool]) -> None:
        self.client = self.client.bind_tools(LangChainToolsConverter.to_lc(tools))

    @property
    def name(self) -> str:
        return self._name
