from typing import List
from pydantic import BaseModel, ConfigDict, computed_field


class CycleInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    cycle_path: List[str]
    
    @computed_field
    @property
    def cycle_length(self) -> int:
        return len(self.cycle_path) 