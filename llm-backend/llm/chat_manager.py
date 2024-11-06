class ChatManager:
    TOKEN_DELTA_PER_MESSAGE = 10  # Adjust based on actual token usage per message format

    def __init__(self, context_length, max_new_tokens, hf_repo_id, tokenizer):
        self.context_length = context_length
        self.max_new_tokens = max_new_tokens
        self.chat_history = []  # Initialize chat history
        self.total_tokens = 0  # Initialize total token count
        self.tokenizer = tokenizer

    def add_message(self, role, content):
        """Add a message to the chat history and update the token count."""
        tokens = self.count_tokens(content)
        self.chat_history.append({"role": role, "content": content})
        self.total_tokens += tokens + self.TOKEN_DELTA_PER_MESSAGE
        self.print_in_box(f"Token size now after adding to chat: {self.total_tokens}")
        self.trim_history()
        self.check_token_limit()  # Check if the total tokens are close to the limit

    def check_token_limit(self):
        """Check if the token count is close to the maximum allowed limit and print a warning if so."""
        max_allowed_tokens = self.context_length - self.max_new_tokens
        if self.total_tokens >= max_allowed_tokens:
            self.print_in_box(f"Warning: Chat history is at max allowed tokens ({self.total_tokens} tokens).")

    def trim_history(self):
        """Ensure chat history token count does not exceed context length minus max new tokens."""
        max_allowed_tokens = self.context_length - self.max_new_tokens

        while self.total_tokens > max_allowed_tokens:
            if not self.chat_history:
                break

            oldest_message = self.chat_history[0]
            message_tokens = self.count_tokens(oldest_message["content"]) + self.TOKEN_DELTA_PER_MESSAGE

            if self.total_tokens - message_tokens >= max_allowed_tokens:
                self.chat_history.pop(0)
                self.total_tokens -= message_tokens
            else:
                truncate_length = self.total_tokens - max_allowed_tokens
                truncated_tokens = self.tokenizer.encode(oldest_message["content"])[truncate_length:]
                truncated_content = self.tokenizer.decode(truncated_tokens)
                oldest_message["content"] = truncated_content
                self.total_tokens = max_allowed_tokens

    def count_tokens(self, content):
        """Count tokens for a given content string using the tokenizer."""
        return len(self.tokenizer.encode(content))

    def clear_history(self):
        """Clear the chat history and reset token count."""
        self.total_tokens = 0
        self.chat_history = []

    @staticmethod
    def print_in_box(message):
        """Print a message in a visually prominent box."""
        border = '*' * (len(message) + 6)
        print(f"\n{border}")
        print(f"*  {message}  *")
        print(border)
