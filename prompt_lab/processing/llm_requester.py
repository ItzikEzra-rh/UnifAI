import requests
import re


class LLMRequester:
    def __init__(self, api_url, max_context_length):
        self.api_url = api_url
        self.max_context_length = max_context_length  # max tokens the llm can generate

    def send_request(self, prompt, max_tokens=None):
        response = requests.post(
            self.api_url,
            json={"prompt": prompt,
                  "contextLength": f"{max_tokens if max_tokens else self.max_context_length}"},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response

    @staticmethod
    def prompt_format(context, input_text):
        return f"<|start_header_id|>context<|end_header_id|>{context}<|eot_id|><|start_header_id|>user<|end_header_id|>{input_text}<|start_header_id|>assistant<|end_header_id|>"

    @staticmethod
    def extract_assistant_text(text):
        # Try to extract text between <|start_header_id|>assistant<|end_header_id|> and <|eot_id|>
        matches = re.findall(r'<\|start_header_id\|>assistant<\|end_header_id\|>(.*?)<\|eot_id\|>', text, re.DOTALL)

        # If no match, fall back to extracting between <|start_header_id|>assistant<|end_header_id|> and <|end_of_text|>
        if not matches:
            matches = re.findall(r'<\|start_header_id\|>assistant<\|end_header_id\|>(.*?)<\|end_of_text\|>', text,
                                 re.DOTALL)

        return ' '.join(matches).strip()

    # TODO need to take tags from project config