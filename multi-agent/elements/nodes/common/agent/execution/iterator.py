"""
Agent execution iterator with fine-grained control.

This module provides the AgentIterator class which controls the step-by-step
execution of agent strategies. Supports multiple execution modes for different
use cases and provides streaming events for real-time monitoring.

Design Principles:
- Iterator Pattern: Step-by-step control over execution
- Mode-based: Different execution patterns (auto, manual, guided)
- Event Streaming: Real-time execution monitoring
- Error Resilient: Graceful handling of failures
"""

import time
from typing import Iterator, Optional, List, Callable, Dict, Any, Tuple
from enum import Enum

from ..primitives import (
    AgentAction, 
    AgentObservation, 
    AgentStep, 
    StepType, 
    ActionStatus,
    ActionObservationPair
)
from ..strategies.base import AgentStrategy, SupportsToolValidation
from elements.llms.common.chat.message import ChatMessage


class ExecutionMode(Enum):
    """Different modes of agent execution."""
    AUTO = "auto"          # Automatically execute all actions
    MANUAL = "manual"      # Yield actions, wait for observations  
    GUIDED = "guided"      # Ask for confirmation before execution


class AgentIterator:
    """
    Iterator for step-by-step agent execution.
    
    Provides fine-grained control over agent execution with support for:
    - Multiple execution modes (auto/manual/guided)
    - Real-time streaming of execution events
    - Tool validation and policy enforcement
    - Manual intervention and control
    - Error handling and recovery
    
    The iterator maintains execution state and coordinates between the
    agent strategy, tool execution, and user control.
    
    Example:
        # Automatic execution
        iterator = AgentIterator(
            strategy=react_strategy,
            tool_executor=executor.execute,
            mode=ExecutionMode.AUTO
        )
        
        for step in iterator:
            if step.type == StepType.FINISH:
                print("Agent finished:", step.data.output)
                break
    """
    
    def __init__(
        self,
        *,
        strategy: AgentStrategy,
        tool_executor: Callable[[AgentAction], AgentObservation],
        tool_validator: Optional[SupportsToolValidation] = None,
        stream: Optional[Callable[[Dict[str, Any]], None]] = None,
        mode: ExecutionMode = ExecutionMode.AUTO,
        on_action: Optional[Callable[[AgentAction], bool]] = None  # Return False to skip
    ):
        """
        Initialize agent iterator.
        
        Args:
            strategy: Agent strategy for decision-making
            tool_executor: Function to execute actions
            tool_validator: Optional action validator
            stream: Optional streaming callback for events
            mode: Execution mode (auto/manual/guided)
            on_action: Optional callback to approve/reject actions
        """
        self.strategy = strategy
        self.tool_executor = tool_executor
        self.tool_validator = tool_validator
        self.stream = stream or (lambda x: None)
        self.mode = mode
        self.on_action = on_action
        
        # Execution state
        self.messages: List[ChatMessage] = []
        self.observations: List[ActionObservationPair] = []
        self.history: List[AgentStep] = []
        self.pending_actions: List[AgentAction] = []
        self._finished = False
        self._iteration_count = 0
    
    def __iter__(self) -> Iterator[AgentStep]:
        """Return iterator interface."""
        return self
    
    def __next__(self) -> AgentStep:
        """
        Get next step in agent execution.
        
        Core execution loop:
        1. Check if we should continue
        2. Process any pending actions (for guided mode)
        3. Get next steps from strategy
        4. Process each step based on type
        5. Handle actions according to execution mode
        6. Return the next step
        
        Returns:
            Next AgentStep in execution
            
        Raises:
            StopIteration: When execution is complete
        """
        if self._finished:
            raise StopIteration
        
        # Process pending actions first (for guided mode)
        if self.pending_actions and self.mode == ExecutionMode.AUTO:
            action = self.pending_actions.pop(0)
            return self._execute_action_step(action)
        
        # Check if strategy wants to continue
        if not self.strategy.should_continue(self.history):
            self._finished = True
            raise StopIteration
        
        try:
            # Get next steps from strategy
            steps = self.strategy.think(self.messages, self.observations)
            
            for step in steps:
                self.history.append(step)
                self._emit_step_event(step)
                
                # Handle different step types
                if step.type == StepType.ACTION:
                    return self._handle_action_step(step)
                    
                elif step.type == StepType.FINISH:
                    self._finished = True
                    return step
                    
                elif step.type == StepType.ERROR:
                    return self._handle_error_step(step)
                    
                else:
                    # PLANNING or other non-terminal steps
                    return step
            
        except Exception as e:
            # Handle unexpected strategy errors
            error_step = AgentStep(StepType.ERROR, e, metadata={
                "error_type": "strategy_error",
                "iteration": self._iteration_count
            })
            self.history.append(error_step)
            self._emit_step_event(error_step)
            self._finished = True
            return error_step
        
        # No more steps from strategy
        self._finished = True
        raise StopIteration
    
    def feed_observation(
        self, 
        action: AgentAction, 
        observation: AgentObservation
    ) -> None:
        """
        Manually provide observation for an action (MANUAL mode).
        
        Used when mode=MANUAL to provide custom observations or when
        you want to override the automatic tool execution.
        
        Args:
            action: The action that was executed
            observation: The result of executing the action
        """
        self.observations.append((action, observation))
        obs_step = AgentStep(StepType.OBSERVATION, observation, metadata={
            "action_id": action.id,
            "mode": "manual"
        })
        self.history.append(obs_step)
        self._emit_step_event(obs_step)
    
    def confirm_action(self, action_id: str, execute: bool = True) -> Optional[AgentStep]:
        """
        Confirm or reject pending action (GUIDED mode).
        
        Used when mode=GUIDED to approve/reject actions before execution.
        
        Args:
            action_id: ID of the action to confirm
            execute: Whether to execute (True) or skip (False) the action
            
        Returns:
            AgentStep with observation, or None if action not found
        """
        # Find and remove action from pending
        action = None
        for i, a in enumerate(self.pending_actions):
            if a.id == action_id:
                action = self.pending_actions.pop(i)
                break
        
        if not action:
            return None
        
        if execute:
            # Execute the action
            return self._execute_action_step(action)
        else:
            # Create rejection observation
            obs = AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output="Action rejected by user",
                success=False,
                error=Exception("User rejected action")
            )
            self.feed_observation(action, obs)
            return AgentStep(StepType.OBSERVATION, obs, metadata={
                "action_id": action.id,
                "mode": "guided",
                "user_rejected": True
            })
    
    def get_pending_actions(self) -> List[AgentAction]:
        """Get list of pending actions (useful for GUIDED mode)."""
        return list(self.pending_actions)
    
    def _handle_action_step(self, step: AgentStep) -> AgentStep:
        """
        Handle an action step based on execution mode.
        
        Args:
            step: AgentStep containing an AgentAction
            
        Returns:
            The step to yield to caller
        """
        action = step.data
        
        # Validate action if validator provided
        if self.tool_validator:
            is_valid, error_msg = self.tool_validator.validate_action(action)
            if not is_valid:
                return self._create_validation_error_step(action, error_msg)
        
        # Check action approval callback
        if self.on_action and not self.on_action(action):
            return self._create_skipped_action_step(action, "Rejected by policy")
        
        # Handle based on execution mode
        if self.mode == ExecutionMode.AUTO:
            # Execute immediately and create observation step
            obs_step = self._execute_action_step(action)
            self.history.append(obs_step)
            self._emit_step_event(obs_step)
            return step  # Return the action step, observation is in history
            
        elif self.mode == ExecutionMode.MANUAL:
            # Just return the action step, caller must provide observation
            return step
            
        elif self.mode == ExecutionMode.GUIDED:
            # Add to pending for confirmation
            self.pending_actions.append(action)
            return step
        
        return step
    
    def _handle_error_step(self, step: AgentStep) -> AgentStep:
        """
        Handle an error step.
        
        Determines whether execution should continue after the error
        based on error type and strategy configuration.
        """
        error = step.data
        
        # Check if this is a recoverable error
        recoverable = getattr(error, 'recoverable', False)
        
        if not recoverable:
            self._finished = True
            
        return step
    
    def _execute_action_step(self, action: AgentAction) -> AgentStep:
        """
        Execute an action and create corresponding observation step.
        
        Args:
            action: Action to execute
            
        Returns:
            AgentStep containing the observation
        """
        start_time = time.time()
        
        try:
            # Update action status
            action = action.with_status(ActionStatus.EXECUTING)
            
            # Execute the action
            observation = self.tool_executor(action)
            
            # Update action status based on result
            if observation.success:
                action = action.with_status(ActionStatus.SUCCESS)
            else:
                action = action.with_status(ActionStatus.FAILED, str(observation.error))
            
            # Ensure execution time is recorded
            if observation.execution_time == 0.0:
                from dataclasses import replace
                observation = replace(
                    observation, 
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            # Create error observation for execution failure
            observation = AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=None,
                success=False,
                error=e,
                execution_time=time.time() - start_time
            )
            action = action.with_status(ActionStatus.FAILED, str(e))
        
        # Add to observations history
        self.observations.append((action, observation))
        
        # Create observation step
        obs_step = AgentStep(
            StepType.OBSERVATION, 
            observation,
            metadata={
                "action_id": action.id,
                "execution_time": observation.execution_time,
                "success": observation.success
            }
        )
        
        return obs_step
    
    def _create_validation_error_step(self, action: AgentAction, error_msg: str) -> AgentStep:
        """Create step for validation error."""
        obs = AgentObservation(
            action_id=action.id,
            tool=action.tool,
            output=None,
            success=False,
            error=Exception(f"Validation failed: {error_msg}")
        )
        
        self.observations.append((action, obs))
        return AgentStep(StepType.OBSERVATION, obs, metadata={
            "action_id": action.id,
            "validation_error": True,
            "error_message": error_msg
        })
    
    def _create_skipped_action_step(self, action: AgentAction, reason: str) -> AgentStep:
        """Create step for skipped action."""
        obs = AgentObservation(
            action_id=action.id,
            tool=action.tool,
            output=f"Action skipped: {reason}",
            success=False,
            error=Exception(reason)
        )
        
        self.observations.append((action, obs))
        return AgentStep(StepType.OBSERVATION, obs, metadata={
            "action_id": action.id,
            "skipped": True,
            "reason": reason
        })
    
    def _emit_step_event(self, step: AgentStep) -> None:
        """
        Emit streaming event for a step.
        
        Args:
            step: Step to emit event for
        """
        self._iteration_count += 1
        
        event = {
            "type": f"agent_{step.type.value}",
            "step": step,
            "iteration": self._iteration_count,
            "timestamp": step.timestamp,
            "metadata": step.metadata
        }
        
        # Add type-specific data
        if step.type == StepType.ACTION:
            action = step.data
            event.update({
                "action_id": action.id,
                "tool": action.tool,
                "tool_input": action.tool_input,
                "reasoning": action.reasoning
            })
            
        elif step.type == StepType.OBSERVATION:
            obs = step.data
            event.update({
                "action_id": obs.action_id,
                "tool": obs.tool,
                "success": obs.success,
                "execution_time": obs.execution_time
            })
            
        elif step.type == StepType.FINISH:
            finish = step.data
            event.update({
                "output": finish.output,
                "reasoning": finish.reasoning
            })
        
        self.stream(event)
