import requests
import subprocess
import time
from llm.model_loader import AbstractModelLoader
from openai import OpenAI
import os
from transformers import AutoTokenizer


class VLLMModelLoader(AbstractModelLoader):
    vllm_process = None
    TOKEN_DELTA_PER_MESSAGE = 10  # Adjust based on actual token usage per message format

    def __init__(self, *args, vllm_port=8000, **kwargs):
        super().__init__(*args, **kwargs)
        self.vllm_port = vllm_port
        self.server_url = f"http://0.0.0.0:{self.vllm_port}/"
        self.chat_history = []  # Initialize chat history
        self.total_tokens = 0  # Initialize the total token count
        self.max_new_tokens = kwargs.get("max_new_tokens", 4096)  # Default for max new tokens
        self.tokenizer = AutoTokenizer.from_pretrained(self.hf_repo_id)

    def load_model(self):
        with VLLMModelLoader._load_lock:
            if self.vllm_process is not None:
                print("vLLM server is already running.")
                return False
            try:
                self.vllm_process = subprocess.Popen(
                    ["vllm", "serve", self.hf_repo_id,
                     "--port", str(self.vllm_port),
                     "--max-model-len", str(self.context_length),
                     "--quantization", "bitsandbytes",
                     "--load-format", "bitsandbytes"]
                )
                if self.wait_for_server():
                    self.model_loader = self
                    return True
                else:
                    self.model_loader = None
                    return False
            except Exception as e:
                raise RuntimeError(f"Failed to start vLLM server: {e}")

    def wait_for_server(self, timeout=180, interval=5):
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

    def add_to_chat_history(self, role, content):
        """Add a message to the chat history and update the token count."""
        tokens = self.count_tokens(content)
        self.chat_history.append({"role": role, "content": content})
        self.total_tokens += tokens + VLLMModelLoader.TOKEN_DELTA_PER_MESSAGE
        self.print_in_box(f"Token size now after adding to chat: {self.total_tokens}")
        self.trim_chat_history()
        self.print_in_box(f"Token size now after trimming: {self.total_tokens}")

    def trim_chat_history(self):
        """Ensure chat history token count does not exceed context length minus max new tokens."""
        max_allowed_tokens = self.context_length - self.max_new_tokens

        # Trim messages from the start until total_tokens (including formatting) is within max_allowed_tokens
        while self.total_tokens > max_allowed_tokens:
            if not self.chat_history:
                break

            # Remove or truncate the oldest message to reduce token count
            oldest_message = self.chat_history[0]
            message_tokens = self.count_tokens(oldest_message["content"]) + VLLMModelLoader.TOKEN_DELTA_PER_MESSAGE

            if self.total_tokens - message_tokens >= max_allowed_tokens:
                # Remove the entire oldest message if it reduces tokens sufficiently
                self.chat_history.pop(0)
                self.total_tokens -= message_tokens
            else:
                # Partially truncate the oldest message if removing it entirely would exceed the limit
                truncate_length = self.total_tokens - max_allowed_tokens
                truncated_tokens = self.tokenizer.encode(oldest_message["content"])[truncate_length:]
                truncated_content = self.tokenizer.decode(truncated_tokens)
                oldest_message["content"] = truncated_content
                # Update total_tokens after truncation to ensure it's within max_allowed_tokens
                self.total_tokens = max_allowed_tokens

    def count_tokens(self, content):
        """Use the tokenizer to count tokens for a given content string."""
        return len(self.tokenizer.encode(content))

    def infer(self, prompt, temperature, max_new_tokens=None):
        openai_api_key = "EMPTY"
        openai_api_base = os.path.join(self.server_url, "v1")
        client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_api_base,
        )

        if max_new_tokens:
            self.max_new_tokens = max_new_tokens

        # Add the user prompt to the chat history
        self.add_to_chat_history("user", prompt)

        max_allowed_tokens = self.context_length - self.max_new_tokens
        # Warning if tokens are close to the max allowed limit
        if self.total_tokens >= max_allowed_tokens:
            self.print_in_box(f"Warning: Chat history is at max allowed tokens ({self.total_tokens} tokens).")

        # Call OpenAI API with the entire chat history and enable streaming
        response = client.chat.completions.create(
            messages=self.chat_history,
            model=self.hf_repo_id,
            stream=True,
            max_tokens=max_new_tokens,
            temperature=temperature
        )

        # Stream the response content and update chat history at the end
        return self.generate_response(response)

    def generate_response(self, response):
        """Handles the OpenAI streaming response and yields it as bytes while accumulating content."""
        response_content = ""  # Initialize to accumulate the full response

        # Stream each chunk to the client
        for chunk in response:
            if hasattr(chunk, "choices") and chunk.choices:
                content = getattr(chunk.choices[0].delta, "content", "")
                if content:
                    response_content += content  # Accumulate full response
                    yield content.encode('utf-8')  # Stream each chunk as bytes

        # After streaming completes, add the accumulated response to chat history
        self.add_to_chat_history("assistant", response_content)

    def clean_model(self):
        with VLLMModelLoader._load_lock:
            if self.vllm_process:
                self.vllm_process.terminate()
                self.vllm_process.wait()
                self.vllm_process = None
                return True
            return False

    def stop_infer(self):
        pass

    def clear_chat_history(self):
        self.total_tokens = 0
        self.chat_history = []

    @staticmethod
    def print_in_box(message):
        """Print a message in a visually prominent box."""
        border = '*' * (len(message) + 6)  # Adjust the border length based on message length
        print(f"\n{border}")
        print(f"*  {message}  *")
        print(border)
