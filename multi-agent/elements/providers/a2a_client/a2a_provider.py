"""
A2A Provider - Simple orchestrator for A2A communication

Provides clean interface using ChatMessage (your system's type).
Internally uses A2A SDK Pydantic models via A2AClient wrapper.
No tools, no registry - pure communication layer.

Uses proper Pydantic models and enums throughout.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncIterator, Iterator
from pydantic import HttpUrl
from a2a.types import AgentCard, Task, TaskState
from global_utils.utils.async_bridge import get_async_bridge

from .a2a_client import A2AClient, A2AConnectionError
from .message_converter import A2AMessageConverter
from elements.llms.common.chat.message import ChatMessage


class A2AProvider:
    """
    A2A Provider - High-level interface for A2A agents.
    
    Interface: Works with ChatMessage (your internal type)
    Implementation: Uses A2A SDK internally with proper message conversion
    
    Responsibilities:
    - Initialize and cache agent connection
    - Convert ChatMessage ↔ A2A message format
    - Provide send/stream methods with clean interface
    - Handle multi-turn conversations
    """
    
    def __init__(self, base_url: HttpUrl, agent_card: Optional[AgentCard] = None):
        """
        Initialize A2A provider.
        
        Args:
            base_url: A2A agent URL (e.g., http://localhost:10000)
            agent_card: Optional pre-fetched agent card
        """
        self.base_url = base_url
        self.agent_card = agent_card
        self.converter = A2AMessageConverter()
        self._initialized = False
    
    async def _ensure_initialized(self) -> None:
        """Fetch agent card if not already done."""
        if self._initialized:
            return
        
        async with A2AClient(base_url=self.base_url, agent_card=self.agent_card) as client:
            self.agent_card = client.get_agent_card()
            print(f"A2AProvider: Connected to A2A agent: {self.agent_card.name}")
            print(f"A2AProvider: Agent version: {self.agent_card.version}")
            
            # Log available skills
            skills = client.get_available_skills()
            if skills:
                print(f"A2AProvider: Available skills: {skills}")
        
        self._initialized = True
    
    async def send_message(
        self,
        message: ChatMessage,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
        skill_name: Optional[str] = None,
        wait_for_completion: bool = True,
        poll_interval: float = 0.5,
        max_poll_attempts: int = 60
    ) -> tuple[ChatMessage, Dict[str, Any]]:
        """
        Send message and get response.
        
        Args:
            message: Your ChatMessage
            task_id: Optional task ID for multi-turn continuation
            context_id: Optional context ID for multi-turn continuation
            skill_name: Optional skill to target (for future use)
            wait_for_completion: Wait for task to complete (poll if status is 'working')
            poll_interval: Seconds between polling attempts (default: 0.5)
            max_poll_attempts: Max number of polling attempts (default: 60)
            
        Returns:
            Tuple of (ChatMessage response, metadata dict)
            metadata contains: task_id, context_id, status, status_message
        """
        await self._ensure_initialized()
        
        async with A2AClient(base_url=self.base_url, agent_card=self.agent_card) as client:
            # Convert ChatMessage to A2A Message Pydantic model
            a2a_message = self.converter.to_a2a_message(
                message, 
                task_id=task_id,
                context_id=context_id
            )
            
            print(f"A2AProvider: Sending message: {message.content[:50]}...")
            
            # Send message - returns Task Pydantic model
            task: Task = await client.send_message(a2a_message)
            
            # Extract metadata
            metadata = self.converter.extract_metadata(task)
            task_state = self.converter.get_task_state(task)
            
            print(f"A2AProvider: Received response - Task: {metadata['task_id']}, Status: {task_state}")
            
            # Poll for completion if task is still working
            if wait_for_completion and task_state == TaskState.working:
                print(f"A2AProvider: Task {metadata['task_id']} is working, polling for completion...")
                task = await self._poll_for_completion(
                    client=client,
                    task_id=metadata['task_id'],
                    poll_interval=poll_interval,
                    max_attempts=max_poll_attempts
                )
                # Update metadata with final status
                metadata = self.converter.extract_metadata(task)
                print(f"A2AProvider: Task completed - Status: {metadata['status']}")
            
            # Convert Task to ChatMessage
            chat_response = self.converter.from_a2a_task(task)
            
            return chat_response, metadata
    
    async def _poll_for_completion(
        self,
        client: A2AClient,
        task_id: str,
        poll_interval: float,
        max_attempts: int
    ) -> Task:
        """
        Poll task until completion or timeout.
        
        Args:
            client: Connected A2AClient
            task_id: Task ID to poll
            poll_interval: Seconds between attempts
            max_attempts: Maximum polling attempts
            
        Returns:
            Final Task Pydantic model
            
        Raises:
            A2AConnectionError: If polling times out or task fails
        """
        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)
            
            # Get task status - returns Task Pydantic model
            task: Task = await client.get_task(task_id)
            task_state = task.status.state if task.status else TaskState.submitted
            
            print(f"A2AProvider: Poll attempt {attempt + 1}/{max_attempts} - Status: {task_state}")
            
            # Check if task is complete
            if task_state == TaskState.completed:
                print(f"A2AProvider: Task {task_id} completed successfully")
                return task
            elif task_state == TaskState.failed:
                error_msg = task.status.message if task.status else "Unknown error"
                print(f"A2AProvider: Task {task_id} failed: {error_msg}")
                raise A2AConnectionError(f"Task failed: {error_msg}")
            elif task_state == TaskState.canceled:
                print(f"A2AProvider: Task {task_id} was canceled")
                raise A2AConnectionError("Task was canceled")
            elif task_state != TaskState.working:
                # Unexpected status
                print(f"A2AProvider: Task {task_id} has unexpected status: {task_state}")
        
        # Timeout
        raise A2AConnectionError(
            f"Polling timeout after {max_attempts} attempts ({max_attempts * poll_interval}s)"
        )
    
    async def stream_message(
        self,
        message: ChatMessage,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
        skill_name: Optional[str] = None
    ) -> AsyncIterator[ChatMessage]:
        """
        Stream message and get real-time responses.
        
        Args:
            message: Your ChatMessage
            task_id: Optional task ID for continuation
            context_id: Optional context ID for continuation
            skill_name: Optional skill to target (for future use)
            
        Yields:
            ChatMessage chunks as they arrive
        """
        await self._ensure_initialized()
        
        async with A2AClient(base_url=self.base_url, agent_card=self.agent_card) as client:
            # Convert to A2A Message Pydantic model
            a2a_message = self.converter.to_a2a_message(
                message,
                task_id=task_id,
                context_id=context_id
            )
            
            print(f"A2AProvider: Streaming message: {message.content[:50]}...")
            
            # Stream via client - yields Task Pydantic models
            async for task in client.stream_message(a2a_message):
                # Convert Task to ChatMessage
                try:
                    chat_chunk = self.converter.from_a2a_task(task)
                    yield chat_chunk
                except Exception as e:
                    print(f"A2AProvider: Failed to convert task chunk: {e}")
                    continue
    
    def get_available_skills(self) -> list[str]:
        """
        Get list of available skill names.
        
        Returns:
            List of skill names from agent card
        """
        if not self._initialized:
            with get_async_bridge() as bridge:
                bridge.run(self._ensure_initialized())
        
        if self.agent_card and self.agent_card.skills:
            return [s.name for s in self.agent_card.skills if s.name]
        return []
    
    # Sync wrappers for convenience
    def send_message_sync(
        self,
        message: ChatMessage,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
        wait_for_completion: bool = True,
        poll_interval: float = 0.3,
        max_poll_attempts: int = 1000,
        **kwargs
    ) -> tuple[ChatMessage, Dict[str, Any]]:
        """
        Sync version of send_message.
        
        Args:
            message: ChatMessage to send
            task_id: Optional task ID
            context_id: Optional context ID
            wait_for_completion: Wait for task completion
            poll_interval: Seconds between polling attempts
            max_poll_attempts: Maximum polling attempts
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (response ChatMessage, metadata dict)
        """
        with get_async_bridge() as bridge:
            return bridge.run(self.send_message(
                message,
                task_id,
                context_id,
                wait_for_completion=wait_for_completion,
                poll_interval=poll_interval,
                max_poll_attempts=max_poll_attempts,
                **kwargs
            ))
    
    def stream_message_sync(
        self,
        message: ChatMessage,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
        **kwargs
    ) -> Iterator[ChatMessage]:
        """
        Sync version of stream_message - yields chunks in sync context with real-time streaming.
        
        Uses AsyncBridge.iterate() for true real-time streaming (no buffering).
        Items are yielded as they arrive from the async generator.
        
        Args:
            message: ChatMessage to send
            task_id: Optional task ID for continuation
            context_id: Optional context ID for continuation
            **kwargs: Additional arguments
            
        Yields:
            ChatMessage chunks as they arrive in real-time
            
        Example:
            for chunk in provider.stream_message_sync(message):
                print(chunk.content, end='', flush=True)
        """
        with get_async_bridge() as bridge:
            # Create async generator
            async_gen = self.stream_message(
                message,
                task_id=task_id,
                context_id=context_id,
                **kwargs
            )
            
            # Use iterate() for real-time streaming (no buffering)
            for chunk in bridge.iterate(async_gen):
                yield chunk
    
    # Factory methods
    @classmethod
    async def create_async(
        cls,
        base_url: HttpUrl,
        agent_card: Optional[AgentCard] = None
    ) -> "A2AProvider":
        """
        Async factory method - creates fully initialized provider.
        
        Args:
            base_url: A2A agent URL
            agent_card: Optional pre-fetched agent card
            
        Returns:
            Initialized A2AProvider
        """
        provider = cls(base_url, agent_card)
        await provider._ensure_initialized()
        return provider
    
    @classmethod
    def create_sync(
        cls,
        base_url: HttpUrl,
        agent_card: Optional[AgentCard] = None
    ) -> "A2AProvider":
        """
        Sync factory method - creates fully initialized provider.
        
        Args:
            base_url: A2A agent URL
            agent_card: Optional pre-fetched agent card
            
        Returns:
            Initialized A2AProvider
        """
        with get_async_bridge() as bridge:
            return bridge.run(cls.create_async(base_url, agent_card))
    
    def __repr__(self) -> str:
        agent_name = self.agent_card.name if self.agent_card else "unknown"
        return f"A2AProvider(agent='{agent_name}', url='{self.base_url}')"

