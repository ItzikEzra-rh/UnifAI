from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Union
from pydantic import BaseModel
from .action_models import ActionType
import asyncio
import inspect


class BaseAction(ABC):
    """
    Base action interface supporting both sync and async execution
    """

    # Action metadata (to be defined by subclasses)
    name: str
    description: str
    action_type: ActionType
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    @abstractmethod
    def execute(self, input_data: BaseModel) -> Union[BaseModel, Any]:
        """
        Execute the action with validated input.
        Can be implemented as either sync or async method.
        
        Args:
            input_data: Validated input according to input_schema
            
        Returns:
            Result according to output_schema (sync or awaitable)
        """
        pass

    def execute_sync(self, input_data: BaseModel) -> BaseModel:
        """
        Execute the action synchronously.
        If the action is async, this will run it in an event loop.
        
        Args:
            input_data: Validated input according to input_schema
            
        Returns:
            Result according to output_schema
        """
        result = self.execute(input_data)

        # If the result is a coroutine, run it in event loop
        if inspect.iscoroutine(result):
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we need to run in thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, result)
                        return future.result()
                else:
                    # Loop exists but not running
                    return loop.run_until_complete(result)
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(result)

        # Otherwise, return the sync result
        return result

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get action metadata for API consumers"""
        return {
            "name": cls.name,
            "description": cls.description,
            "action_type": cls.action_type.value,
            "input_schema": cls.input_schema.model_json_schema(),
            "output_schema": cls.output_schema.model_json_schema()
        }

    def validate_input(self, input_data: Dict[str, Any]) -> BaseModel:
        """Validate input data against input schema"""
        return self.input_schema.model_validate(input_data)
