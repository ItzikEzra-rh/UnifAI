from typing import Any
from .base_tool import BaseTool
from pydantic import BaseModel, Field


class AdditionInput(BaseModel):
    a: int = Field(..., description="First number")
    b: int = Field(..., description="Second number")


class AdditionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="add",
            description="Adds two integers.",
            args_schema=AdditionInput
        )

    def run(self, *args: Any, **kwargs: Any) -> int:
        inputs = self.args_schema(**kwargs)
        return inputs.a + inputs.b
