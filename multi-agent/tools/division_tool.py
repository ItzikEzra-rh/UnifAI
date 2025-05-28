from typing import Any
from .base_tool import BaseTool
from pydantic import BaseModel, Field


class DivisionInput(BaseModel):
    x: int = Field(..., description="First number")
    y: int = Field(..., description="Second number")


class DivisionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="divide",
            description="divide two numbers.",
            args_schema=DivisionInput
        )

    def run(self, *args: Any, **kwargs: Any) -> float:
        inputs = self.args_schema(**kwargs)
        return inputs.x / inputs.y
