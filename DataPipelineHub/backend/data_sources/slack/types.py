from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SlackMetadata:
    channel_id: str
    channel_name: Optional[str] = None
    is_private: Optional[bool] = None
