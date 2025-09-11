"""
ReAct (Reasoning + Acting) agent strategy.

This module implements the ReAct pattern where agents interleave reasoning
and action in a loop:
1. Observe current state
2. Think about what to do next (reasoning)
3. Take action or provide final answer
4. Observe results and repeat

The ReAct strategy is effective for many tasks because it allows the agent
to reason about each step and adapt based on observations.

Reference:
    "ReAct: Synergizing Reasoning and Acting in Language Models"
    https://arxiv.org/abs/2210.03629
"""

import time
from typing import List, Tuple, Callable, Optional, Dict, Any
from elements.llms.common.chat.message import ChatMessage, Role
from elements.tools.common.base_tool import BaseTool
from ..primitives import AgentAction, AgentObservation, AgentStep, StepType
from ..parsers import OutputParser, ParseError
from .base import AgentStrategy
from ..constants import StrategyDefaults, SystemPrompts, StrategyType


class ReActStrategy(AgentStrategy):
    """
    ReAct strategy implementation.
    
    Implements the Reasoning + Acting pattern where the agent:
    1. Analyzes the current situation
    2. Reasons about what action to take
    3. Takes action using available tools
    4. Observes results
    5. Repeats until task is complete
    
    Features:
    - Interleaved reasoning and acting
    - Error handling with reflection
    - Configurable system prompts
    - Step-by-step execution tracking
    
    Example:
        strategy = ReActStrategy(
            llm_chat=node._chat,
            parser=ToolCallParser(),
            max_steps=10,
            system_prompt_template=custom_template
        )
    """
    
    def __init__(
        self,
        *,
        llm_chat: Callable[[List[ChatMessage], List[BaseTool]], ChatMessage],
        tools: List[BaseTool],
        parser: OutputParser,
        max_steps: int = StrategyDefaults.MAX_STEPS,
        system_prompt_template: Optional[str] = None,
        min_reasoning_length: int = StrategyDefaults.MIN_REASONING_LENGTH
    ):
        """
        Initialize ReAct strategy.
        
        Args:
            llm_chat: Function to call LLM with messages and tools
            tools: All available tools for this strategy
            parser: Output parser for LLM responses
            max_steps: Maximum reasoning steps before stopping
            system_prompt_template: Custom system prompt (optional)
            min_reasoning_length: Minimum characters expected in reasoning
        """
        super().__init__(
            llm_chat=llm_chat,
            tools=tools,
            parser=parser, 
            max_steps=max_steps
        )
        self.min_reasoning_length = min_reasoning_length
        self.system_prompt_template = system_prompt_template or SystemPrompts.REACT_DEFAULT
    
    def get_tools_for_phase(self, phase: str, context: Dict[str, Any] = None) -> List[BaseTool]:
        """
        ReAct uses all tools in all phases.
        
        Args:
            phase: Current phase (always StrategyType.REACT.value for this strategy)
            context: Optional context (unused)
            
        Returns:
            All available tools
        """
        return list(self.all_tools.values())
    
    def think(
        self,
        messages: List[ChatMessage],
        observations: List[AgentObservation]
    ) -> List[AgentStep]:
        """
        Perform one cycle of ReAct reasoning.
        
        Process:
        1. Build context from messages and observations
        2. Add ReAct system prompt if this is the first step
        3. Call LLM to get reasoning and next action
        4. Parse response into actions or finish
        5. Handle any parsing errors
        
        Args:
            messages: Conversation history
            observations: Previous action-observation pairs
            
        Returns:
            List of steps (usually planning + action, or planning + finish)
        """
        steps = []
        
        try:
            # Build context for LLM
            context = self._build_react_context(messages, observations)
            
            # Get tools for ReAct (all tools)
            tools = self.get_tools_for_phase(StrategyType.REACT.value)
            
            # Get LLM response with tools
            start_time = time.time()
            response = self.llm_chat(context, tools)
            reasoning_time = time.time() - start_time
            
            # Create planning step
            steps.append(AgentStep(
                type=StepType.PLANNING,
                data=response,
                metadata={
                    "strategy": StrategyType.REACT.value,
                    "step_count": self._step_count,
                    "reasoning_time": reasoning_time,
                    "reasoning_content": response.content
                }
            ))
            
            # Validate reasoning quality
            self._validate_reasoning(response)
            
            # Parse response into actions or finish
            result = self.parser.parse(response)
            
            if isinstance(result, list):
                # Multiple actions - add each as separate step
                for action in result:
                    steps.append(AgentStep(
                        type=StepType.ACTION,
                        data=action,
                        metadata={
                            "strategy": StrategyType.REACT.value,
                            "reasoning": response.content or "",
                            "step_count": self._step_count
                        }
                    ))
            else:
                # Single finish
                steps.append(AgentStep(
                    type=StepType.FINISH,
                    data=result,
                    metadata={
                        "strategy": StrategyType.REACT.value,
                        "reasoning": response.content or "",
                        "step_count": self._step_count
                    }
                ))
            
        except ParseError as e:
            # Handle parsing errors with reflection if enabled
            error_steps = self.handle_parse_error(e)
            steps.extend(error_steps)
            
        except Exception as e:
            # Handle unexpected errors
            steps.append(AgentStep(
                type=StepType.ERROR,
                data=e,
                metadata={
                    "strategy": StrategyType.REACT.value,
                    "error_type": "execution_error",
                    "step_count": self._step_count
                }
            ))
        
        self.increment_step_count()
        return steps
    
    def should_continue(self, history: List[AgentStep]) -> bool:
        """
        Check if ReAct strategy should continue.
        
        Stopping conditions:
        - Maximum steps reached
        - Terminal step encountered (finish/unrecoverable error)
        - Too many consecutive errors
        
        Args:
            history: Complete execution history
            
        Returns:
            True if execution should continue
        """
        # Check for terminal steps
        if history and history[-1].is_terminal:
            return False
        
        # Check step limit
        if self._step_count >= self.max_steps:
            return False
        
        # Check for too many consecutive errors
        consecutive_errors = 0
        for step in reversed(history):
            if step.is_error():
                consecutive_errors += 1
            else:
                break
        
        if consecutive_errors >= 3:  # Configurable threshold
            return False
        
        return True
    
    def _build_react_context(
        self,
        messages: List[ChatMessage],
        observations: List[AgentObservation]
    ) -> List[ChatMessage]:
        """
        Build ReAct-specific context for LLM.
        
        Adds ReAct system prompt on first step and formats observations
        in a way that's conducive to the ReAct pattern.
        
        Args:
            messages: Original messages
            observations: Action-observation pairs
            
        Returns:
            Complete context for LLM
        """
        context = list(messages)
        
        # Add system prompt on first step
        if self._step_count == 0:
            context.insert(0, ChatMessage(
                role=Role.SYSTEM,
                content=self.system_prompt_template
            ))
        
        # Add formatted observations
        if observations:
            obs_text = self._format_react_observations(observations)
            context.append(ChatMessage(
                role=Role.ASSISTANT,
                content=obs_text
            ))
        
        return context
    
    def _format_react_observations(
        self,
        observations: List[AgentObservation]
    ) -> str:
        """
        Format observations in ReAct style.
        
        Formats as:
        Action: tool_name
        Action Input: {input}
        Observation: result
        
        Args:
            observations: Action-observation pairs
            
        Returns:
            ReAct-formatted observation string
        """
        formatted = []
        
        for i, obs in enumerate(observations, 1):
            # Format action info from observation
            formatted.append(f"Action: {obs.tool}")
            
            # Format observation result
            if obs.success:
                formatted.append(f"Observation: {obs.output}")
            else:
                formatted.append(f"Observation: Error - {obs.error}")
            
            formatted.append("")  # Empty line between observations
        
        return "\n".join(formatted)
    
    def _validate_reasoning(self, response: ChatMessage) -> None:
        """
        Validate the quality of reasoning in the response.
        
        Checks that the LLM provided sufficient reasoning before
        taking action. This helps ensure thoughtful decision-making.
        
        Args:
            response: LLM response to validate
            
        Raises:
            ParseError: If reasoning is insufficient
        """
        content = response.content or ""
        
        # Check minimum length
        if len(content) < self.min_reasoning_length:
            raise ParseError(
                f"Reasoning too short ({len(content)} chars, min {self.min_reasoning_length})",
                content,
                recoverable=True
            )
        
        # Could add more sophisticated reasoning quality checks here
        # - Presence of reasoning keywords
        # - Analysis of current situation
        # - Clear action justification
    
