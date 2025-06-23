from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from uuid import uuid4
from core.enums import ResourceCategory


class ResourceDoc(BaseModel):
    uuid: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str  # tenant / user
    category: Literal[
        ResourceCategory.LLM, ResourceCategory.TOOL, ResourceCategory.PROVIDER, ResourceCategory.CONDITION, ResourceCategory.RETRIEVER, ResourceCategory.NODE]  # category of resource
    type: str
    name: str  # unique per (user, category, type)
    version: int = 1
    config: dict  # flattened provider/llm …
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime = Field(default_factory=datetime.utcnow)
