from policies.skip.skip_policy import SkipPolicy


class TokenSizeSkipPolicy(SkipPolicy):
    """
    Example: If prompt.token_count > max_token_limit, skip the prompt and record it in the repository.
    """

    def __init__(self, max_token_limit: int, repository):
        self.max_token_limit = max_token_limit
        self.repository = repository

    def should_skip(self, prompt: Prompt) -> bool:
        if prompt.token_count > self.max_token_limit:
            # Mark skip reason
            prompt.metadata.setdefault("skip", {})
            prompt.metadata["skip"]["reason"] = "token_size_exceeded"
            # Save to "skipped" data in the repository
            self.repository.save_skipped_data({
                "uuid": prompt.uuid,
                "metadata": prompt.metadata
            })
            print(f"[SkipPolicy] Skipped prompt due to token size: {prompt.uuid}")
            return True
        return False
