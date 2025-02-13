from .response import ResponseProcessor


class ResponseStreamProcessor(ResponseProcessor):
    """
    Processes streamed LLM responses.
    """

    def process_response(self, response):
        """
        Processes a streamed response chunk-by-chunk.

        Args:
            response: The streamed response from the LLM.
        """
        for chunk in response:
            for choice in chunk.choices or []:
                if choice.index is not None and choice.text:
                    self.responses[choice.index] += choice.text

        return [self.responses[i] for i in range(len(self.responses.items()))]
