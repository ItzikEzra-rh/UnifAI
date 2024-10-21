# utils/tokenizer.py
from transformers import AutoTokenizer


class TokenizerUtils:
    def __init__(self, tokenizer_path, context_limit=130000, fixed_max_tokens=8192):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.context_limit = context_limit
        self.fixed_max_tokens = fixed_max_tokens
        self.prompt_token_count = 0

    def tokenize(self, text):
        """Tokenize the text and store the token count for the prompt."""
        tokens = self.tokenizer.encode(text, truncation=False)
        self.prompt_token_count = len(tokens)
        print(f"current prompt tokens are: {self.prompt_token_count}")
        return tokens

    def is_within_limit(self):
        """Check if the prompt token count is within the model's context limit."""
        return self.prompt_token_count <= self.context_limit

    def calculate_max_tokens(self):
        """
        Calculate the maximum tokens for generation based on the prompt size.
        If the prompt token count is less than the fixed max tokens (8192), return 8192.
        Otherwise, return the prompt token count + 8192.
        """
        if self.prompt_token_count < self.fixed_max_tokens:
            return self.fixed_max_tokens
        return min(self.prompt_token_count + self.fixed_max_tokens, self.context_limit)

    def encode_and_get_max_tokens(self, text):
        """
        A method that tokenizes the text and calculates the maximum tokens for generation.
        This method will also check if the tokenized prompt fits within the context limit.
        """
        tokens = self.tokenize(text)
        if not self.is_within_limit():
            raise ValueError("The prompt exceeds the model's context limit.")
        return self.calculate_max_tokens()

    # TODO take max context length of LLM model from the config, also the max generated tokens fix
    # TODO max generated tokens, should be max context len - prompt tokens
