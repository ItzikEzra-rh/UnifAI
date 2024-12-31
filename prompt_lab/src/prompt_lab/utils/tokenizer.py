from transformers import AutoTokenizer


class TokenizerUtils:
    def __init__(self, tokenizer_path, max_context_length=8192, max_generation_length=4096):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.max_context_length = max_context_length
        self.max_generation_length = max_generation_length
        self.prompt_token_count = 0

    def tokenize(self, text):
        """Tokenize the text and update the token count for the prompt."""
        return self.tokenizer.encode(text, truncation=False)

    def count_tokens(self, text):
        return len(self.tokenize(text))

    def format_chat_prompt(self, messages):
        """Format chat messages for LLMs that support chat templates."""
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def get_toking_limit(self):
        return self.max_context_length - self.max_generation_length
