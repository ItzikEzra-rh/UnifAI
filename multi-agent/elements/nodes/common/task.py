"""
Task model for agentic communication.

Clean, minimal design focused on what nodes need to coordinate intelligently.
Nodes use LLM intelligence to understand and execute tasks.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid


class Task(BaseModel):
    """
    Task for agentic communication.
    
    Nodes use LLM intelligence to understand and execute tasks.
    Clean ID management for task relationships and coordination.
    """
    
    # Task Identity
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Core Task Content
    content: str  # Natural language description of what to do
    data: Dict[str, Any] = Field(default_factory=dict)  # Supporting data
    
    # Coordination
    should_respond: bool = False  # Does this task need a response?
    
    # Task Relationships
    correlation_task_id: Optional[str] = None  # Links response to original request
    parent_task_id: Optional[str] = None       # Task that spawned this subtask
    thread_id: Optional[str] = None            # Execution context grouping
    
    # Results (only when responding)
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, content: str, data: dict = None, should_respond: bool = False,
               parent_task_id: str = None, thread_id: str = None) -> 'Task':
        """Create a new task."""
        return cls(
            content=content,
            data=data or {},
            should_respond=should_respond,
            parent_task_id=parent_task_id,
            thread_id=thread_id
        )
    
    @classmethod
    def create_subtask(cls, parent_task: 'Task', content: str, 
                      data: dict = None, should_respond: bool = False) -> 'Task':
        """Create subtask of another task."""
        return cls(
            content=content,
            data=data or {},
            should_respond=should_respond,
            parent_task_id=parent_task.task_id,  # Link to parent
            thread_id=parent_task.thread_id      # Same execution context
        )
    
    @classmethod
    def respond_success(cls, original_task: 'Task', result: dict) -> 'Task':
        """Create successful response task."""
        return cls(
            content=f"Response to: {original_task.content}",
            result=result,
            should_respond=False,
            correlation_task_id=original_task.task_id,  # Link to original
            thread_id=original_task.thread_id
        )
    
    @classmethod  
    def respond_error(cls, original_task: 'Task', error: dict) -> 'Task':
        """Create error response task.""" 
        return cls(
            content=f"Error response to: {original_task.content}",
            error=error,
            should_respond=False,
            correlation_task_id=original_task.task_id,
            thread_id=original_task.thread_id
        )
    
    # Helper methods
    def is_response(self) -> bool:
        """Check if this is a response task."""
        return self.correlation_task_id is not None
    
    def is_subtask(self) -> bool:
        """Check if this is a subtask."""
        return self.parent_task_id is not None
    
    def is_root_task(self) -> bool:
        """Check if this is a root task (no parent)."""
        return self.parent_task_id is None
    
    def is_successful_response(self) -> bool:
        """Check if this is a successful response."""
        return self.result is not None
    
    def is_error_response(self) -> bool:
        """Check if this is an error response."""
        return self.error is not None
