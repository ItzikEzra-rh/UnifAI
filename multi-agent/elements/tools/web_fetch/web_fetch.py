from typing import Any, Dict

import httpx
from html_to_markdown import convert

from elements.tools.common.base_tool import BaseTool
from .models import WebFetchArgs, WebFetchResponse


class WebFetchTool(BaseTool):
    name: str = "web_fetch"
    description: str = "Fetch a web page and return its content as markdown."
    args_schema = WebFetchArgs

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        args = WebFetchArgs(**kwargs)

        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(args.url)
        except Exception as exc:
            return WebFetchResponse(success=False, url=args.url, error=str(exc)).model_dump()

        content = convert(response.text)
        return WebFetchResponse(success=True, url=args.url, content=content).model_dump()
