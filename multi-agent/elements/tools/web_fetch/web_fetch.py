from typing import Any, Dict

import httpx

from elements.tools.common.base_tool import BaseTool
from .content_processor import extract_title, html_to_markdown
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

        html = response.text
        title = extract_title(html)
        content = html_to_markdown(html)

        return WebFetchResponse(
            success=True,
            url=args.url,
            title=title,
            content=content,
        ).model_dump()
