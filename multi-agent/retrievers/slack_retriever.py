import requests
from typing import Any
from retrievers.base_retriever import BaseRetriever
from pydantic import HttpUrl


class SlackRetriever(BaseRetriever):
    """
    Calls an external Slack‐query API to fetch matching messages.
    """

    def __init__(self, name: str,
                 api_url: HttpUrl,
                 top_k_results: int,
                 threshold: float):
        self._name = name
        self.api_url = str(api_url)
        self.top_k = top_k_results
        self.threshold = threshold

    def retrieve(self, query: str) -> Any:
        params = {
            "query": query,
            "top_k_results": self.top_k
        }

        resp = requests.get(self.api_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        # data = {
        #     "search_results": [
        #         {
        #             "id": "3788d5f8-6262-43d7-b0ba-21e6f7b51b8e",
        #             "metadata": {
        #                 "channel_name": "automation-and-tools-israel",
        #                 "message_count": 1,
        #                 "source_type": "slack_conversation",
        #                 "time_range": "1745333344.631109-1745333344.631109",
        #                 "token_count": 160
        #             },
        #             "score": 0.43369973,
        #             "text": "Slack Conversation in #automation-and-tools-israel - 2025-04-22 10:49:04 to 2025-04-22 10:49:04\n==================================================\n[10:49:04] U05R7R4RABE: Task: Jira-summarizer Exploration\nDetails: I managed to create a local environment and set up the LLM.\nNext Step: Need to dive deeper into the code, sync with Tim to better understand the product, and test with multiple Jira tickets.\n\nTask: Parser/Prompt Lab for Various Projects\nDetails: Working with tag-openshift-builds on several projects.\nNext Step: Parser is completed. Prompt Lab is pending and may depend on GPU allocation — waiting for a response from Tom."
        #         },
        #         {
        #             "id": "2e09663a-5072-4490-babf-df4df246310b",
        #             "metadata": {
        #                 "channel_name": "automation-and-tools-israel",
        #                 "message_count": 1,
        #                 "source_type": "slack_conversation",
        #                 "time_range": "1715066857.191869-1715066857.191869",
        #                 "token_count": 179
        #             },
        #             "score": 0.36612207,
        #             "text": "Slack Conversation in #automation-and-tools-israel - 2024-05-07 03:27:37 to 2024-05-07 03:27:37\n==================================================\n[03:27:37] U05UZ820V4Y: Hey, whoever involved in pushing code to TestMangaer please go over the following guideline and make sure to take all the steps when starting to work on new Jira Ticket:\nhttps://docs.google.com/document/d/1mkENePMxA5ZmJi_gd0LTkV2vRtoHXmVsrW0qxcgL3Yo/edit\n(I add it under the team's shared section)\n\nYesterday we start with dedicated time slots for MR and it was great &amp; save us a lot of time. Let's continue to work in that way. Thanks."
        #         }
        #     ]
        # }
        # # filter by `threshold` if result items carry a "score"
        if "search_results" in data:
            data = data["search_results"]
        if isinstance(data, list):
            return [item for item in data if item.get("score", 0.0) >= self.threshold]
        return data

    @property
    def name(self) -> str:
        return self._name
