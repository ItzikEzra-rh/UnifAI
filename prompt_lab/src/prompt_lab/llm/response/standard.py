from .response import ResponseProcessor


class StandardResponseProcessor(ResponseProcessor):
    """
    Processes non-streamed batch LLM responses.
    """

    def process_response(self, response):
        """
        Processes a full batch response at once.

        Args:
            response: The full batch response from the LLM.
        """
        for choice in response.get("choices", []):
            if choice.get("index") is not None and choice.get("text"):
                self.responses[choice["index"]] = choice["text"]
        return [self.responses[i] for i in range(len(self.responses.items()))]
