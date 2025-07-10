from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field
from core.enums import ResourceCategory


class ResourceDoc(BaseModel):
    """
    One persisted element in the user *Library*.
    – cfg_dict is **plain json**; we do NOT store the Pydantic instance.
    """
    rid: str = Field(default_factory=lambda: uuid4().hex)  # public key
    user_id: str  # tenant
    category: ResourceCategory
    type: str  # e.g. "openai"
    name: str  # user label (unique per user+cat+type)
    version: int = 1
    cfg_dict: Dict[str, Any]  # raw config
    nested_refs: List[str] = Field(default_factory=list)
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime = Field(default_factory=datetime.utcnow)
