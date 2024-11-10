import requests
import subprocess
import time
from llm.loader.model_loader import AbstractModelLoader
from llm.chat_manager import ChatManager
from openai import OpenAI
import threading
import os
import psutil


class VLLMModelLoader(AbstractModelLoader):
    vllm_process = None

    def __init__(self, *args, vllm_port=8000, **kwargs):
        super().__init__(*args, **kwargs)
        self.vllm_port = vllm_port
        self.server_url = f"http://0.0.0.0:{self.vllm_port}/"
        self.chat_manager = ChatManager(self.context_length, self.max_new_tokens, self.tokenizer)
        self.stop_event = {}
        # self.stop_event = threading.Event()

    def load_model(self):
        """Load the vLLM model."""
        if self.vllm_process is not None:
            print("vLLM server is already running.")
            return False
        try:
            self.vllm_process = subprocess.Popen(
                ["vllm", "serve", self.hf_repo_id,
                 "--port", str(self.vllm_port),
                 "--max-model-len", str(self.chat_manager.context_length),
                 "--quantization", "bitsandbytes",
                 "--load-format", "bitsandbytes"]
            )
            return self.wait_for_server()
        except Exception as e:
            raise RuntimeError(f"Failed to start vLLM server: {e}")

    def wait_for_server(self, timeout=180, interval=5):
        """Wait for the vLLM server to start within a given timeout."""
        server_url = os.path.join(self.server_url, "health")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(server_url)
                if response.status_code == 200:
                    print("vLLM server is up!")
                    return True
            except requests.ConnectionError:
                print(f"Trying to connect to VLLM server, {time.time() - start_time} seconds passed...")
                time.sleep(interval)
        print("vLLM server did not start within the timeout period.")
        return False

    def infer(self, prompt, temperature, max_new_tokens=None, session_id=" "):
        """Send a prompt to the model and stream the response."""
        self.stop_event[session_id] = threading.Event()
        self.stop_event[session_id].clear()  # Clear any previous stop event
        openai_api_key = "EMPTY"
        openai_api_base = os.path.join(self.server_url, "v1")

        # Instantiate the client
        client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_api_base,
        )

        if max_new_tokens:
            self.max_new_tokens = max_new_tokens
            self.chat_manager.max_new_tokens = max_new_tokens

        # Add user prompt to chat history (token limit check is handled by ChatManager)
        self.chat_manager.add_message("user", prompt, session_id)

        # Call OpenAI API with the entire chat history and enable streaming
        response = client.chat.completions.create(
            messages=self.chat_manager.get_chat_history(session_id),
            model=self.hf_repo_id,
            stream=True,
            max_tokens=max_new_tokens,
            temperature=temperature
        )

        # Stream the response content and check stop event to break
        return self.generate_response(response, session_id)

    def generate_response(self, response, session_id):
        """Stream the OpenAI API response and update the chat history."""
        response_content = ""

        # Stream each chunk to the client
        for chunk in response:
            if self.stop_event[session_id].is_set():  # Check if stop signal has been triggered
                response.close()
                print("Stopping inference as requested.")
                break

            if hasattr(chunk, "choices") and chunk.choices:
                content = getattr(chunk.choices[0].delta, "content", "")
                if content:
                    response_content += content
                    yield content.encode('utf-8')

        # Add assistant's response to chat history if inference was not stopped
        if not self.stop_event[session_id].is_set():
            self.chat_manager.add_message("assistant", response_content, session_id)

    def clean_model(self):
        """Terminate the model process and wait for the port to be released."""
        if self.model_loader:
            if self.vllm_process:
                self.vllm_process.terminate()
                self.vllm_process.wait()
                self.vllm_process = None
                time.sleep(5)
                self.wait_for_port_release(self.vllm_port, timeout=60)
                return True
        return False

    def wait_for_port_release(self, port, timeout=60):
        """Wait until the given port is released by checking connection status.
        to make release time faster(the TIME_WAIT value) use: `sudo sysctl -w net.ipv4.tcp_fin_timeout=2`
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.is_port_in_use(port):
                print(f"Port {port} has been released.")
                return True
            print(f"Waiting for port {port} to be released...")
            time.sleep(1)
        print(f"Warning: Port {port} was not released within {timeout} seconds.")
        return False

    @staticmethod
    def is_port_in_use(port):
        """Check if the port is currently in use."""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                print(f"Port {port} is in use with status: {conn.status}")
                return True
        print(f"Port {port} is free.")
        return False

    def stop_infer(self, session_id):
        """Stop the inference by setting the stop event and deleting the client."""
        self.stop_event[session_id].set()  # Signal to stop streaming

    def clear_chat_history(self, session_id):
        self.chat_manager.clear_history(session_id)

    def load_chat_context(self, chat, session_id):
        return self.chat_manager.load_chat_context(chat, session_id)
