class ChatManager:
    TOKEN_DELTA_PER_MESSAGE = 10  # Adjust based on actual token usage per message format

    def __init__(self, context_length, max_new_tokens, tokenizer):
        self.context_length = context_length
        self.max_new_tokens = max_new_tokens
        self.chat_history = {}  # Initialize chat history
        self.total_tokens = {}  # Dictionary to track token count per session
        self.tokenizer = tokenizer

    def add_message(self, role, content, session_id):
        """Add a message to the chat history and update the token count for the specific session."""
        tokens = self.count_tokens(content)

        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
            self.total_tokens[session_id] = 0  # Initialize token count for new session

        self.chat_history[session_id].append({"role": role, "content": content})
        self.total_tokens[session_id] += tokens + self.TOKEN_DELTA_PER_MESSAGE
        self.print_in_box(f"Token size now after adding to chat for session {session_id}: {self.total_tokens[session_id]}")

        self.trim_history(session_id)
        self.check_token_limit(session_id)  # Check if the total tokens are close to the limit for this session

    def check_token_limit(self, session_id):
        """Check if the token count is close to the maximum allowed limit for the session and print a warning if so."""
        max_allowed_tokens = self.context_length - self.max_new_tokens
        if self.total_tokens[session_id] >= max_allowed_tokens:
            self.print_in_box(f"Warning: Chat history for session {session_id} is at max allowed tokens ({self.total_tokens[session_id]} tokens).")

    def trim_history(self, session_id):
        """Ensure chat history token count does not exceed context length minus max new tokens for the session."""
        max_allowed_tokens = self.context_length - self.max_new_tokens

        while self.total_tokens[session_id] > max_allowed_tokens:
            if not self.chat_history[session_id]:
                break

            oldest_message = self.chat_history[session_id][0]
            message_tokens = self.count_tokens(oldest_message["content"]) + self.TOKEN_DELTA_PER_MESSAGE

            if self.total_tokens[session_id] - message_tokens >= max_allowed_tokens:
                self.chat_history[session_id].pop(0)
                self.total_tokens[session_id] -= message_tokens
            else:
                truncate_length = self.total_tokens[session_id] - max_allowed_tokens
                truncated_tokens = self.tokenizer.encode(oldest_message["content"])[truncate_length:]
                truncated_content = self.tokenizer.decode(truncated_tokens)
                oldest_message["content"] = truncated_content
                self.total_tokens[session_id] = max_allowed_tokens

    def count_tokens(self, content):
        """Count tokens for a given content string using the tokenizer."""
        return len(self.tokenizer.encode(content))

    def get_chat_history(self, session_id):
        return self.chat_history.get(session_id, [])

    def clear_history(self, session_id):
        """Clear the chat history and reset token count for the specific session."""
        self.total_tokens[session_id] = 0
        self.chat_history[session_id] = []

    @staticmethod
    def print_in_box(message):
        """Print a message in a visually prominent box."""
        border = '*' * (len(message) + 6)
        print(f"\n{border}")
        print(f"*  {message}  *")
        print(border)
