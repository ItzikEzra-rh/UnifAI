"""
Agent execution iterator with fine-grained control.

This module provides the AgentIterator class which controls the step-by-step
execution of agent strategies. Supports multiple execution modes for different
use cases and provides streaming events for real-time monitoring.

Design Principles:
- Iterator Pattern: Step-by-step control over execution
- Mode-based: Different execution patterns (auto, guided)
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
    AgentFinish
)
from ..strategies.base import AgentStrategy
from elements.llms.common.chat.message import ChatMessage, Role


class ExecutionMode(Enum):
    """Different modes of agent execution."""
    AUTO = "auto"          # Automatically execute all actions
    GUIDED = "guided"      # Ask for confirmation before execution


class AgentIterator:
    """
    Iterator for step-by-step agent execution.
    
    Provides fine-grained control over agent execution with support for:
    - Multiple execution modes (auto/guided)
    - Real-time streaming of execution events
    - Tool validation and policy enforcement
    - User confirmation and control
    - Error handling and recovery
    
    The iterator maintains execution state and coordinates between the
    agent strategy, tool execution, and user control.
    
    Example:
        # Automatic execution
        iterator = AgentIterator(
            strategy=react_strategy,
            action_executor=action_executor,
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
        action_executor: 'AgentActionExecutor',
        stream: Optional[Callable[[Dict[str, Any]], None]] = None,
        mode: ExecutionMode = ExecutionMode.AUTO,
        on_action: Optional[Callable[[AgentAction], bool]] = None  # Return False to skip
    ):
        """
        Initialize agent iterator.
        
        Args:
            strategy: Agent strategy for decision-making
            action_executor: AgentActionExecutor instance for tool execution
            stream: Optional streaming callback for events
            mode: Execution mode (auto/guided)
            on_action: Optional callback to approve/reject actions
        """
        self.strategy = strategy
        self.action_executor = action_executor
        self.stream = stream or (lambda x: None)
        self.mode = mode
        self.on_action = on_action
        
        # Execution state
        self.messages: List[ChatMessage] = []
        self.observations: List[AgentObservation] = []
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
            print(f"🔍 DEBUG: Iterator got {len(steps)} steps from strategy: {[step.type for step in steps]}")

            # Update conversation messages with assistant responses
            self._update_conversation_messages(steps)

            # Collect all actions to execute them together
            actions_to_execute = []
            terminal_step = None
            
            for step in steps:
                print(f"🔍 DEBUG: Processing step type: {step.type}")
                self.history.append(step)
                self._emit_step_event(step)
                
                # Collect actions for batch execution
                if step.type == StepType.ACTION:
                    print(f"🔍 DEBUG: Collecting ACTION step for tool: {step.data.tool}")
                    actions_to_execute.append(step)
                    
                elif step.type == StepType.FINISH:
                    print(f"🔍 DEBUG: Found FINISH step")
                    self._finished = True
                    terminal_step = step
                    
                elif step.type == StepType.ERROR:
                    print(f"🔍 DEBUG: Found ERROR step")
                    terminal_step = step
                    
                # PLANNING steps are processed but don't cause return
            
            # Execute all collected actions
            if actions_to_execute:
                print(f"🔍 DEBUG: Executing {len(actions_to_execute)} actions together")
                return self._handle_batch_actions(actions_to_execute)
            
            # Return terminal step if found
            if terminal_step:
                return terminal_step
            
            # If we processed all steps without finding actions or terminal steps,
            # return the last step (should be PLANNING)
            if steps:
                print(f"🔍 DEBUG: No actions or terminal steps, returning last step: {steps[-1].type}")
                return steps[-1]
            
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
        self.observations.append(observation)
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
        print(f"🔍 DEBUG: _handle_action_step called with action: {action.tool}, mode: {self.mode}")
        
        # Validation is handled by ToolExecutorManager during execution
        
        # Check action approval callback
        if self.on_action and not self.on_action(action):
            print(f"🔍 DEBUG: Action rejected by policy")
            return self._create_skipped_action_step(action, "Rejected by policy")
        
        # Handle based on execution mode
        if self.mode == ExecutionMode.AUTO:
            print(f"🔍 DEBUG: AUTO mode - executing action immediately")
            # Execute immediately and create observation step
            obs_step = self._execute_action_step(action)
            self.history.append(obs_step)
            self._emit_step_event(obs_step)
            print(f"🔍 DEBUG: Action executed, observation created: {obs_step.data.success}")
            return step  # Return the action step, observation is in history
            
        elif self.mode == ExecutionMode.GUIDED:
            print(f"🔍 DEBUG: GUIDED mode - adding to pending actions")
            # Add to pending for confirmation
            self.pending_actions.append(action)
            return step
        
        return step
    
    def _handle_batch_actions(self, action_steps: List[AgentStep]) -> AgentStep:
        """
        Handle multiple action steps by executing them together.
        
        Executes all actions in parallel and creates observations for each.
        Returns the first action step while adding all observations to history.
        
        Args:
            action_steps: List of ACTION steps to execute
            
        Returns:
            The first action step (for iterator protocol)
        """
        print(f"🔍 DEBUG: _handle_batch_actions called with {len(action_steps)} actions")
        
        # Extract actions from steps
        actions = [step.data for step in action_steps]
        
        # Validate actions using callback if provided
        if self.on_action:
            approved_actions = []
            for action in actions:
                if self.on_action(action):
                    approved_actions.append(action)
                else:
                    print(f"🔍 DEBUG: Action {action.tool} rejected by policy")
                    # Create skipped observation
                    obs = AgentObservation(
                        action_id=action.id,
                        tool=action.tool,
                        output="Action rejected by policy",
                        success=False,
                        error=Exception("Rejected by policy")
                    )
                    self.observations.append(obs)
            actions = approved_actions
        
        if not actions:
            print(f"🔍 DEBUG: No actions to execute after validation")
            return action_steps[0]  # Return first step even if no actions executed
        
        # Execute based on mode
        if self.mode == ExecutionMode.AUTO:
            print(f"🔍 DEBUG: AUTO mode - executing {len(actions)} actions in batch")
            # Execute all actions together
            batch_observations = self.action_executor.execute_batch(actions)
            
            # Add all observations to history
            for obs in batch_observations:
                self.observations.append(obs)
                obs_step = AgentStep(
                    StepType.OBSERVATION,
                    obs,
                    metadata={
                        "action_id": obs.action_id,
                        "execution_time": obs.execution_time,
                        "success": obs.success
                    }
                )
                self.history.append(obs_step)
                self._emit_step_event(obs_step)
                print(f"🔍 DEBUG: Added observation for {obs.tool}: success={obs.success}")
            
            print(f"🔍 DEBUG: Batch execution completed: {len(batch_observations)} observations created")
            
        elif self.mode == ExecutionMode.GUIDED:
            print(f"🔍 DEBUG: GUIDED mode - adding {len(actions)} actions to pending")
            # Add all actions to pending for confirmation
            self.pending_actions.extend(actions)
        
        # Return the first action step (iterator protocol requirement)
        return action_steps[0]
    
    def _handle_error_step(self, step: AgentStep) -> AgentStep:
        """
        Simple error handling - strategy manages error feedback internally.
        
        Just determines if execution should continue based on recoverability.
        No complex error management needed - strategy handles its own error state.
        """
        recoverable = step.metadata.get("recoverable", False)
        
        if not recoverable:
            self._finished = True
            
        return step  # Strategy handles error feedback internally
    
    def _execute_action_step(self, action: AgentAction) -> AgentStep:
        """
        Execute an action and create corresponding observation step.
        
        Args:
            action: Action to execute
            
        Returns:
            AgentStep containing the observation
        """
        print(f"🔍 DEBUG: _execute_action_step starting for tool: {action.tool}")
        start_time = time.time()
        
        try:
            # Update action status
            action = action.with_status(ActionStatus.EXECUTING)
            print(f"🔍 DEBUG: Action status updated to EXECUTING")
            
            # Execute the action
            print(f"🔍 DEBUG: Calling action_executor.execute with action: {action.tool}")
            observation = self.action_executor.execute(action)
            print(f"🔍 DEBUG: Got observation - success: {observation.success}, output: {observation.output[:100] if observation.output else 'None'}...")
            
            # Update action status based on result
            if observation.success:
                print(f"🔍 DEBUG: Action succeeded")
                action = action.with_status(ActionStatus.SUCCESS)
            else:
                print(f"🔍 DEBUG: Action failed with error: {observation.error}")
                action = action.with_status(ActionStatus.FAILED, str(observation.error))
            
            # Ensure execution time is recorded
            if observation.execution_time == 0.0:
                from dataclasses import replace
                observation = replace(
                    observation, 
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            print(f"🔍 DEBUG: Exception during action execution: {e}")
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
        self.observations.append(observation)
        
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
    
    def _create_skipped_action_step(self, action: AgentAction, reason: str) -> AgentStep:
        """Create step for skipped action."""
        obs = AgentObservation(
            action_id=action.id,
            tool=action.tool,
            output=f"Action skipped: {reason}",
            success=False,
            error=Exception(reason)
        )
        
        self.observations.append(obs)
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
    
    def _update_conversation_messages(self, steps: List[AgentStep]) -> None:
        """
        Update conversation messages with assistant responses.
        
        Maintains proper conversation flow by preserving assistant messages
        that contain tool_calls or final answers. This ensures LLM providers
        see the correct assistant → tool → assistant sequence.
        
        Args:
            steps: Steps returned from strategy.think()
        """
        for step in steps:
            # Preserve assistant messages that are part of the conversation
            if (step.type == StepType.PLANNING and 
                isinstance(step.data, ChatMessage) and 
                step.data.role == Role.ASSISTANT):
                # Assistant planning message (with tool_calls)
                self.messages.append(step.data)
                
            elif (step.type == StepType.FINISH and 
                  isinstance(step.data, AgentFinish)):
                # Convert AgentFinish to assistant message for conversation history
                finish_message = ChatMessage(
                    role=Role.ASSISTANT,
                    content=step.data.output
                )
                self.messages.append(finish_message)
