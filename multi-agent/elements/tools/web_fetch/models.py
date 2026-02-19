from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WebFetchArgs(BaseModel):
    url: str = Field(..., description="The URL of the web page to fetch.")


class WebFetchResponse(BaseModel):
    success: bool
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)
