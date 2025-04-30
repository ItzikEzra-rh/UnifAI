from typing import Any, Dict, List, Optional
from langchain_community.chat_models import ChatOpenAI
from llms.base_llm import BaseLLM


class OpenAILLM(BaseLLM):
    """
    LLM client backed by OpenAI's chat API via LangChain's ChatOpenAI wrapper.
    """

    def __init__(
            self,
            api_key: str,
            base_url: Optional[str] = None,
            model_name: str = "gpt-4",
            temperature: float = 0.7,
            max_tokens: int = 1024,
            timeout: int = 60,
            **extra: Any
    ):
        """
        :param api_key:      Your OpenAI API key.
        :param base_url:     Base URL for the OpenAI API (e.g. Azure endpoint or openai.com).
        :param model_name:   The model ID to use (e.g. "gpt-4").
        :param temperature:  Sampling temperature 0–1.
        :param max_tokens:   Max tokens to generate.
        :param timeout:      Request timeout in seconds.
        :param extra:        Provider-specific overrides (e.g. headers, organization).
        """
        # LangChain's ChatOpenAI expects:
        #   openai_api_key, model_name, temperature, max_tokens,
        #   openai_api_base, request_timeout, plus any extra kwargs.
        params: Dict[str, Any] = {
            "openai_api_key": api_key,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "request_timeout": timeout,
            **extra
        }
        if base_url:
            params["openai_api_base"] = base_url

        self.client = ChatOpenAI(**params)
        self._name = "openai"

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
        Send a chat completion request.

        :param messages:     List of {"role": "...", "content": "..."} dicts.
        :param temperature:  Override the default sampling temperature.
        :param max_tokens:   Override the default max tokens.
        :param stream:       Whether to stream partial responses.
        :param kwargs:       Any additional generation params.
        """
        call_params: Dict[str, Any] = {}
        if temperature is not None:
            call_params["temperature"] = temperature
        if max_tokens is not None:
            call_params["max_tokens"] = max_tokens
        call_params.update(kwargs)

        # LangChain's ChatOpenAI .invoke supports `messages`, `stream`, and generation params
        return self.client.invoke(messages, stream=stream, **call_params)

    def embed(self, text: str, **kwargs: Any) -> List[float]:
        """
        OpenAI chat models don't natively support embeddings here.
        Raise or implement via a separate embeddings client if needed.
        """
        raise NotImplementedError("Embedding not supported by OpenAI chat model")

    @property
    def name(self) -> str:
        """Return the driver key for this LLM (“openai”)."""
        return self._name
