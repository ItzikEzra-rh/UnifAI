"""
A2A Message Converter

Converts between internal ChatMessage and A2A SDK Pydantic models.
Based on actual SDK usage from official a2a-samples.

Uses proper Pydantic models and enums from a2a.types.
"""

from typing import Optional, Dict, Any
from uuid import uuid4

from a2a.types import (
    Message,
    Part,
    TextPart,
    Role as A2ARole,
    Task,
    TaskState,
)
from a2a.utils import get_text_parts

from elements.llms.common.chat.message import ChatMessage, Role


class A2AMessageConverter:
    """
    Convert between ChatMessage and A2A SDK Pydantic models.
    
    Uses official SDK types:
    - Message (Pydantic model)
    - Part/TextPart (Pydantic models)
    - Role (enum)
    - Task (Pydantic model)
    """
    
    @staticmethod
    def to_a2a_message(
        chat_message: ChatMessage,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None
    ) -> Message:
        """
        Convert ChatMessage to A2A Message Pydantic model.
        
        Args:
            chat_message: Internal ChatMessage object
            task_id: Optional task ID for multi-turn continuation
            context_id: Optional context ID for multi-turn continuation
            
        Returns:
            A2A Message Pydantic model with proper types
        """
        # Map internal Role enum to A2A Role enum
        role_mapping = {
            Role.USER: A2ARole.user,
            Role.ASSISTANT: A2ARole.agent,
            Role.SYSTEM: A2ARole.user,  # A2A doesn't have system role
            Role.TOOL: A2ARole.user     # Map tool to user
        }
        
        a2a_role = role_mapping.get(chat_message.role, A2ARole.user)
        
        # Create TextPart for the content
        text_part = TextPart(text=chat_message.content)
        
        # Wrap in Part (union type wrapper)
        parts = [Part(text_part)]
        
        # Build Message Pydantic model
        message = Message(
            role=a2a_role,          # ← Enum, not string!
            parts=parts,             # ← List[Part], not list[dict]
            message_id=uuid4().hex,
            task_id=task_id,         # ← Optional fields
            context_id=context_id
        )
        
        return message
    
    @staticmethod
    def from_a2a_task(task: Task) -> ChatMessage:
        """
        Convert A2A Task to ChatMessage.
        
        Args:
            task: A2A Task Pydantic model (from response)
            
        Returns:
            ChatMessage with agent's response
        """
        # First, try to get content from artifacts (final responses)
        if task.artifacts:
            text_parts = []
            for artifact in task.artifacts:
                text_parts.extend(get_text_parts(artifact.parts))
            
            if text_parts:
                return ChatMessage(
                    role=Role.ASSISTANT,
                    content='\n'.join(text_parts)
                )
        
        # Fallback to status message
        if task.status and task.status.message:
            text_parts = get_text_parts(task.status.message.parts)
            if text_parts:
                return ChatMessage(
                    role=Role.ASSISTANT,
                    content='\n'.join(text_parts)
                )
        
        # Last fallback
        return ChatMessage(
            role=Role.ASSISTANT,
            content=""
        )
    
    @staticmethod
    def extract_metadata(task: Task) -> Dict[str, Any]:
        """
        Extract task metadata from A2A Task.
        
        Args:
            task: A2A Task Pydantic model
            
        Returns:
            Dict with task_id, context_id, status
        """
        return {
            'task_id': task.id,
            'context_id': task.context_id,
            'status': task.status.state if task.status else None,
            'status_message': task.status.message if task.status else None
        }
    
    @staticmethod
    def get_task_state(task: Task) -> TaskState:
        """
        Get task state enum from Task.
        
        Args:
            task: A2A Task Pydantic model
            
        Returns:
            TaskState enum
        """
        return task.status.state if task.status else TaskState.submitted

