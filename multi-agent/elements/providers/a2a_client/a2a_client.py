"""
A2A Client - Correct wrapper around official A2A SDK

Based on actual SDK usage from a2a-samples.
Uses proper Pydantic models and enums throughout.

Key SDK requirements:
1. Uses A2ACardResolver and A2AClient from a2a.client
2. Requires httpx.AsyncClient
3. Uses SendMessageRequest/SendStreamingMessageRequest objects
4. Message is Pydantic Message model (not dict!)
5. Works with Task Pydantic models
"""

import logging
from typing import Optional, AsyncIterator
from uuid import uuid4
from pydantic import HttpUrl
import httpx

from a2a.client import A2ACardResolver, A2AClient as SDKA2AClient
from a2a.types import (
    AgentCard,
    Message,
    Task,
    TaskStatus,
    TaskState,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    MessageSendParams,
    GetTaskRequest,
    GetTaskResponse,
    GetTaskSuccessResponse,
    TaskQueryParams,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    Artifact,
)
from a2a.utils import get_text_parts

logger = logging.getLogger(__name__)


class A2AConnectionError(Exception):
    """Error during A2A agent communication."""
    pass


class A2AClient:
    """
    Wrapper around official A2A SDK.
    
    Follows the actual SDK pattern from a2a-samples:
    - Uses httpx.AsyncClient
    - Uses A2ACardResolver to fetch agent card
    - Uses SDKA2AClient with httpx_client and agent_card
    - Uses Request objects (SendMessageRequest, etc.)
    """
    
    def __init__(self, base_url: HttpUrl, agent_card: Optional[AgentCard] = None):
        """
        Initialize A2A client.
        
        Args:
            base_url: Base URL of A2A agent (e.g., http://localhost:10000)
            agent_card: Optional pre-fetched agent card
        """
        self.base_url = str(base_url)
        self._agent_card = agent_card
        self._httpx_client: Optional[httpx.AsyncClient] = None
        self._sdk_client: Optional[SDKA2AClient] = None
    
    async def __aenter__(self):
        """Enter async context - create httpx client and SDK client."""
        # Create httpx client with extended timeout for long-running agent operations
        # (e.g., travel planning, external API calls, complex processing)
        self._httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,    # Connection establishment
                read=300.0,      # Reading response (5 minutes for agent processing)
                write=10.0,      # Sending request
                pool=10.0        # Pool connection acquisition
            )
        )
        await self._httpx_client.__aenter__()
        
        # Fetch agent card if not provided
        if not self._agent_card:
            resolver = A2ACardResolver(
                httpx_client=self._httpx_client,
                base_url=self.base_url
            )
            try:
                self._agent_card = await resolver.get_agent_card()
                logger.info(f"Fetched agent card: {self._agent_card.name}")
                
                # Log skills
                if self._agent_card.skills:
                    skill_names = [s.name for s in self._agent_card.skills if s.name]
                    logger.info(f"Available skills: {skill_names}")
                    
            except Exception as e:
                await self._httpx_client.__aexit__(None, None, None)
                raise A2AConnectionError(f"Failed to fetch agent card: {e}")
        
        # Initialize SDK client
        self._sdk_client = SDKA2AClient(
            httpx_client=self._httpx_client,
            agent_card=self._agent_card
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - cleanup."""
        if self._httpx_client:
            await self._httpx_client.__aexit__(exc_type, exc_val, exc_tb)
            self._httpx_client = None
        self._sdk_client = None
    
    def get_agent_card(self) -> AgentCard:
        """
        Get cached agent card.
        
        Returns:
            AgentCard object
            
        Raises:
            A2AConnectionError: If not loaded yet
        """
        if not self._agent_card:
            raise A2AConnectionError("Agent card not loaded. Use async context manager.")
        return self._agent_card
    
    async def send_message(self, message: Message) -> Task:
        """
        Send message (non-streaming).
        
        Args:
            message: A2A Message Pydantic model
            
        Returns:
            A2A Task Pydantic model with response
        """
        if not self._sdk_client:
            raise A2AConnectionError("Client not connected. Use async context manager.")
        
        try:
            # Create SendMessageRequest with Pydantic message
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(message=message)
            )
            
            # Send via SDK
            response: SendMessageResponse = await self._sdk_client.send_message(request)
            
            # Extract Task from response
            if isinstance(response.root, SendMessageSuccessResponse):
                if isinstance(response.root.result, Task):
                    task = response.root.result
                    logger.debug(f"Message sent - Task: {task.id}, Status: {task.status.state if task.status else 'unknown'}")
                    return task
                else:
                    raise A2AConnectionError(f"Unexpected result type: {type(response.root.result)}")
            else:
                raise A2AConnectionError(f"Send message failed: {response.root}")
            
        except Exception as e:
            raise A2AConnectionError(f"Failed to send message: {e}")
    
    async def stream_message(self, message: Message) -> AsyncIterator[Task]:
        """
        Stream message (Server-Sent Events).
        
        Args:
            message: A2A Message Pydantic model
            
        Yields:
            A2A Task Pydantic models with incremental updates
        """
        if not self._sdk_client:
            raise A2AConnectionError("Client not connected. Use async context manager.")
        
        try:
            # Create SendStreamingMessageRequest with Pydantic message
            request = SendStreamingMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(message=message)
            )
            
            # Stream via SDK
            stream_response = self._sdk_client.send_message_streaming(request)
            
            async for chunk in stream_response:
                # Extract from streaming response
                if isinstance(chunk.root, SendStreamingMessageSuccessResponse):
                    result = chunk.root.result
                    
                    # Handle different event types
                    if isinstance(result, Task):
                        # Complete Task object (usually final chunk)
                        yield result
                        
                    elif isinstance(result, TaskArtifactUpdateEvent):
                        # Streaming text chunks - THIS IS THE MAIN STREAMING CONTENT
                        # Extract text from artifact parts and create a partial Task
                        # Note: Artifact updates don't include status, so we create a "working" status
                        if result.artifact and result.artifact.parts:
                            text_parts = get_text_parts(result.artifact.parts)
                            if text_parts:
                                # Create a partial Task with the streaming content
                                # Status is "working" since we're actively streaming
                                partial_task = Task(
                                    id=result.task_id,
                                    context_id=result.context_id,
                                    artifacts=[result.artifact],
                                    status=TaskStatus(state=TaskState.working)
                                )
                                yield partial_task
                        
                    elif isinstance(result, TaskStatusUpdateEvent):
                        # Status updates (working, completed, etc.)
                        # TaskStatusUpdateEvent has: task_id, context_id, status, final
                        # But does NOT have a full Task object
                        if result.status:
                            # Only yield if it's a final status (completed/failed)
                            if result.status.state in (TaskState.completed, TaskState.failed):
                                # Create minimal Task with status for completion indication
                                final_task = Task(
                                    id=result.task_id,
                                    context_id=result.context_id,
                                    status=result.status
                                )
                                yield final_task
                            # For non-final status updates (working), just skip
                        else:
                            print(f"Status update without status field")
                        continue
                
        except Exception as e:
            raise A2AConnectionError(f"Failed to stream message: {e}")
    
    async def get_task(self, task_id: str) -> Task:
        """
        Get task status and details.
        
        Args:
            task_id: Task ID to query
            
        Returns:
            A2A Task Pydantic model with current status
        """
        if not self._sdk_client:
            raise A2AConnectionError("Client not connected. Use async context manager.")
        
        try:
            # Create GetTaskRequest (note: uses TaskQueryParams with 'id' field)
            request = GetTaskRequest(
                id=str(uuid4()),
                params=TaskQueryParams(id=task_id)
            )
            
            # Get task via SDK
            response: GetTaskResponse = await self._sdk_client.get_task(request)
            
            # Extract Task from response
            if isinstance(response.root, GetTaskSuccessResponse):
                task = response.root.result
                logger.debug(f"Task {task_id} status: {task.status.state if task.status else 'unknown'}")
                return task
            else:
                raise A2AConnectionError(f"Get task failed: {response.root}")
            
        except Exception as e:
            raise A2AConnectionError(f"Failed to get task: {e}")
    
    def get_available_skills(self) -> list[str]:
        """
        Get list of available skill names from agent card.
        
        Returns:
            List of skill names
        """
        if not self._agent_card or not self._agent_card.skills:
            return []
        
        return [skill.name for skill in self._agent_card.skills if skill.name]

