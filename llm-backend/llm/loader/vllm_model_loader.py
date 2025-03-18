import os
import subprocess
import time
import threading
import requests
import psutil
from openai import OpenAI
from llm.chat_manager import ChatManager
from transformers import AutoTokenizer


class VLLMModelLoader:
    """
    A SOLID, modular, and efficient loader for vLLM with optional adapter support.

    Parameters:
      - base_model: Identifier for the base model.
      - max_len: Maximum sequence length.
      - quantized: Boolean indicating if the model is quantized.
      - adapters: Optional list of adapter records.
      - vllm_port: Port number for the vLLM server.

    When adapters are provided, the vLLM process is started with:
      --enable-lora
      --lora-modules adapter_name=adapter_path[,adapter2=adapter_path2,...]

    During inference, if adapters exist the first adapter's name is used as the model name
    for the OpenAI API call. Otherwise, the base model name is used.
    """

    _lock = threading.Lock()
    instance = None

    def __init__(self, base_model: str, max_len: int, quantized: bool, adapters: list = None, vllm_port: int = 8000):
        try:
            print(max_len)
            self.base_model = base_model
            self.max_len = max_len
            self.quantized = quantized
            self.adapters = adapters or []
            self.vllm_port = vllm_port
            self.server_url = f"http://0.0.0.0:{self.vllm_port}/"
            self.vllm_process = None
            self.max_new_tokens = None
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
            self.chat_manager = ChatManager(self.max_len, self.max_new_tokens, self.tokenizer)
            self.stop_events = {}  # Mapping: session_id -> threading.Event
            self.current_adapter_uid = None  # Store the current requested adapter UID
        except Exception as e:
            raise Exception(f"Error initializing VLLMModelLoader: {e}")

    @classmethod
    def load(cls, base_model: str, max_len: int, quantized: bool, adapters: list = None, vllm_port: int = 8000,
             current_adapter_uid: str = None):
        """
        Load or reuse a vLLM model instance. If a model is already loaded:
          - If the base model is the same, returns the current instance (and updates the current adapter UID).
          - Otherwise, unloads the current instance and loads a new one.
        """
        with cls._lock:
            try:
                if cls.instance is not None:
                    if cls.instance.base_model != base_model:
                        cls.instance.unload()
                    else:
                        cls.instance.current_adapter_uid = current_adapter_uid
                        return cls.instance
                instance = cls(base_model, max_len, quantized, adapters, vllm_port)
                instance.current_adapter_uid = current_adapter_uid
                instance._start_server()
                cls.instance = instance
                return instance
            except Exception as e:
                raise Exception(f"Error loading vLLM model instance: {e}")

    def get_current_adapter_uid(self):
        """
        Retrieve the current adapter UID that was requested.
        """
        try:
            return self.current_adapter_uid
        except Exception as e:
            raise Exception(f"Error retrieving current adapter UID: {e}")

    def _start_server(self):
        """Builds the vLLM command line and starts the server process."""
        try:
            cmd = [
                "vllm", "serve", self.base_model,
                "--port", str(self.vllm_port),
                "--max-model-len", str(self.max_len)
            ]
            if self.quantized:
                cmd.extend(["--quantization", "bitsandbytes", "--load-format", "bitsandbytes"])
            if self.adapters:
                cmd.append("--enable-lora")
                cmd.append("--lora-modules")
                for adapter in self.adapters:
                    if adapter.get('local_adapter_path'):
                        cmd.append(f"{adapter.get('name')}={adapter.get('local_adapter_path')}")
            try:
                print(cmd)
                self.vllm_process = subprocess.Popen(cmd)
            except Exception as e:
                raise RuntimeError(f"Failed to start vLLM server process: {e}")
            self._wait_for_server()
        except Exception as e:
            raise Exception(f"Error starting vLLM server: {e}")

    def _wait_for_server(self, timeout: int = 420, interval: int = 5):
        """Wait until the vLLM server is healthy by checking its /health endpoint."""
        try:
            health_url = os.path.join(self.server_url, "health")
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(health_url)
                    if response.status_code == 200:
                        print("vLLM server is up!")
                        return
                except requests.ConnectionError:
                    pass
                print(f"Waiting for vLLM server... {int(time.time() - start_time)}s elapsed")
                time.sleep(interval)
            raise RuntimeError("vLLM server did not start within the timeout period.")
        except Exception as e:
            raise Exception(f"Error waiting for vLLM server: {e}")

    def infer(self, adapter_name, messages: list, temperature: float, max_new_tokens: int, session_id: str = "default"):
        """
        Sends an inference request. The model name used is:
          - The first adapter's name if adapters exist.
          - Otherwise, the base model name.
        """
        try:
            self.stop_events.setdefault(session_id, threading.Event()).clear()
            openai_api_base = os.path.join(self.server_url, "v1")
            client = OpenAI(api_key="EMPTY", base_url=openai_api_base)
            adapter_names = [adapter.get("name") for adapter in self.adapters]
            if adapter_name not in adapter_names and not adapter_names:
                raise Exception(f"Adapter {adapter_name} is not registered")
            model_name = adapter_name if adapter_name else self.base_model
            if max_new_tokens:
                self.max_new_tokens = max_new_tokens
                self.chat_manager.max_new_tokens = max_new_tokens
            # Add user prompt to chat history (token limit check is handled by ChatManager)
            for message in messages:
                self.chat_manager.add_message(message["role"], message["content"], session_id)
            # print(self.chat_manager.get_chat_history(session_id))
            response = client.chat.completions.create(
                model=model_name,
                messages=self.chat_manager.get_chat_history(session_id),
                stream=True,
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            return self._stream_response(response, session_id)
        except Exception as e:
            raise Exception(f"Error during inference: {e}")

    def _stream_response(self, response, session_id: str):
        """Generator to stream the inference response."""
        try:
            response_content = ""
            for chunk in response:
                if self.stop_events[session_id].is_set():
                    response.close()
                    print("Inference stopped.")
                    break
                if hasattr(chunk, "choices") and chunk.choices:
                    content = getattr(chunk.choices[0].delta, "content", "")
                    if content:
                        response_content += content
                        yield content.encode("utf-8")
        except Exception as e:
            raise Exception(f"Error streaming response: {e}")

    def stop_infer(self, session_id: str):
        """Signal to stop the inference session."""
        try:
            if session_id in self.stop_events:
                self.stop_events[session_id].set()
                return True
            return False
        except Exception as e:
            raise Exception(f"Error stopping inference: {e}")

    def unload(self):
        """
        Cleanly unload the model by terminating the vLLM process and waiting for the port to be released.
        """
        try:
            with self.__class__._lock:
                if self.vllm_process:
                    self.vllm_process.terminate()
                    self.vllm_process.wait()
                    self.vllm_process = None
                    self._wait_for_port_release(self.vllm_port)
                self.__class__.instance = None
        except Exception as e:
            raise Exception(f"Error unloading model: {e}")

    def _wait_for_port_release(self, port: int, timeout: int = 180):
        """Wait until the given port is released."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self._is_port_in_use(port):
                    print(f"Port {port} has been released.")
                    return True
                time.sleep(1)
            print(f"Warning: Port {port} was not released within {timeout} seconds.")
            return False
        except Exception as e:
            raise Exception(f"Error waiting for port release: {e}")

    def _is_port_in_use(self, port: int) -> bool:
        """Check if the port is still in use."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except Exception as e:
            raise Exception(f"Error checking port usage: {e}")

    def clear_chat_history(self, session_id):
        try:
            self.chat_manager.clear_history(session_id)
        except Exception as e:
            raise Exception(f"Error clearing chat history for session {session_id}: {e}")

    def load_chat_context(self, chat, session_id):
        try:
            return self.chat_manager.load_chat_context(chat, session_id)
        except Exception as e:
            raise Exception(f"Error loading chat context for session {session_id}: {e}")
