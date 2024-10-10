import requests
import re


class LLMRequester:
    def __init__(self, api_url, max_context_length):
        self.api_url = api_url
        self.max_context_length = max_context_length  # max tokens the llm can generate

    def send_request(self, prompt):
        response = requests.post(
            self.api_url,
            json={"prompt": prompt,
                  "contextLength": f"{self.max_context_length}"},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response

    @staticmethod
    def prompt_format(context, input_text):
        return f"<context>{context}</context><user>{input_text}</user><assistant>"

    @staticmethod
    def extract_assistant_text(text):
        # Try to extract text between <assistant> and </assistant>
        matches = re.findall(r'<assistant>(.*?)</assistant>', text, re.DOTALL)

        # If no match, fall back to extracting between <assistant> and </s>
        if not matches:
            matches = re.findall(r'<assistant>(.*?)</s>', text, re.DOTALL)

        return ' '.join(matches).strip()
