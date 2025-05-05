from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from llms.base_llm import BaseLLM


class OpenAILLM(BaseLLM):
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
        lc_messages = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
            else:
                raise ValueError(f"Unsupported message role: {role}")

        response = self.client.invoke(lc_messages, stream=stream, **call_params)
        return response.content

    def embed(self, text: str, **kwargs: Any) -> List[float]:
        raise NotImplementedError("Embedding not supported by ChatOpenAI")

    @property
    def name(self) -> str:
        return self._name
