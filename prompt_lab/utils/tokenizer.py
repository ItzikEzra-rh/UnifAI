# utils/tokenizer.py
from transformers import AutoTokenizer

class TokenizerUtils:
    def __init__(self, tokenizer_path):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    def is_within_limit(self, text, limit=32000):
        tokens = self.tokenizer.encode(text, truncation=False)
        return len(tokens) <= limit
