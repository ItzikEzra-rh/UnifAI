from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SlackMetadata:
    channel_id: str
    channel_name: Optional[str] = None
    is_private: Optional[bool] = None
    upload_by: Optional[str] = None

@dataclass(frozen=True)
class DocumentMetadata:
    doc_id: str
    doc_name: Optional[str] = None
    doc_path: Optional[str] = None
    upload_by: Optional[str] = None 
