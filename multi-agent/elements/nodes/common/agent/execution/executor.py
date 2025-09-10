"""
Agent action execution bridge for agent actions.

This module provides the bridge between agent actions and the existing
tool system. The AgentActionExecutor converts AgentActions into tool calls and
handles execution using the established ToolCapableMixin infrastructure.

Design Principles:
- Reuse Existing: Leverages ToolCapableMixin rather than duplicating logic
- Error Handling: Robust error recovery with special tools
- Policy Enforcement: Validation and permission checking
- Integration: Seamless conversion between agent and tool types
"""

import time
from typing import Dict, List, Optional, Tuple, Callable
from elements.tools.common.base_tool import BaseTool
from elements.llms.common.chat.message import ChatMessage, ToolCall, Role
from ..primitives import AgentAction, AgentObservation, ActionStatus
from ..strategies.base import SupportsToolValidation
from ..constants import (
    SpecialToolNames, ToolHandlingPolicy, ToolExecutionDefaults,
    ErrorMessages, ValidationLimits
)


class AgentActionExecutor:
    """
    Executes agent actions using existing tool infrastructure.
    
    Bridges the gap between AgentActions and the existing ToolCapableMixin
    system by converting actions to ChatMessages with tool_calls and using
    the established tool execution pipeline.
    
    Features:
    - Reuses existing tool registry and execution logic
    - Handles argument validation and error recovery
    - Supports special tools for error handling
    - Provides execution timing and metadata
    
    Example:
        # In AgentCapableMixin
        executor = AgentActionExecutor(
            tools=self.tools,  # From ToolCapableMixin
            tool_invoke_fn=self.invoke_tools,  # From ToolCapableMixin
            validate_args=True
        )
        
        observation = executor.execute(agent_action)
    """
    
    def __init__(
        self,
        *,
        tools: List[BaseTool],
        tool_invoke_fn: Callable[[ChatMessage], List[ChatMessage]],
        validate_args: bool = ToolExecutionDefaults.VALIDATE_ARGS,
        on_missing_tool: str = ToolExecutionDefaults.ON_MISSING_TOOL.value,
        special_tools: Optional[Dict[str, BaseTool]] = None
    ):
        """
        Initialize agent action executor.
        
        Args:
            tools: List of available tools
            tool_invoke_fn: Function to invoke tools (from ToolCapableMixin)
            validate_args: Whether to validate tool arguments
            on_missing_tool: How to handle missing tools
            special_tools: Additional special tools for error handling
        """
        self.tools = {tool.name: tool for tool in tools}
        self.tool_invoke_fn = tool_invoke_fn
        self.validate_args = validate_args
        self.on_missing_tool = on_missing_tool
        
        # Add built-in special tools
        self.special_tools = special_tools or {}
        self._add_built_in_special_tools()
    
    def execute(self, action: AgentAction) -> AgentObservation:
        """
        Execute an agent action and return observation.
        
        Process:
        1. Check if it's a special tool (starts with _)
        2. Validate tool exists and arguments are correct
        3. Convert action to ChatMessage with tool_calls
        4. Use existing tool_invoke_fn to execute
        5. Convert results back to AgentObservation
        6. Handle any errors gracefully
        
        Args:
            action: Agent action to execute
            
        Returns:
            AgentObservation with execution results
        """
        start_time = time.time()
        
        try:
            # Handle special tools
            if action.tool.startswith("_"):
                return self._execute_special_tool(action, start_time)
            
            # Check if tool exists
            if action.tool not in self.tools:
                return self._handle_missing_tool(action, start_time)
            
            # Validate arguments if enabled
            if self.validate_args:
                validation_error = self._validate_arguments(action)
                if validation_error:
                    return AgentObservation(
                        action_id=action.id,
                        tool=action.tool,
                        output=None,
                        success=False,
                        error=Exception(validation_error),
                        execution_time=time.time() - start_time
                    )
            
            # Convert action to ChatMessage format
            tool_message = self._action_to_chat_message(action)
            
            # Execute using existing tool system
            result_messages = self.tool_invoke_fn(tool_message)
            
            # Convert results back to observation
            return self._chat_messages_to_observation(action, result_messages, start_time)
            
        except Exception as e:
            # Handle unexpected execution errors
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=None,
                success=False,
                error=e,
                execution_time=time.time() - start_time,
                metadata={"error_type": "execution_error"}
            )
    
    def _execute_special_tool(self, action: AgentAction, start_time: float) -> AgentObservation:
        """
        Execute special tools (those starting with _).
        
        Special tools are built-in tools for error handling, reflection, etc.
        """
        tool = self.special_tools.get(action.tool)
        if not tool:
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=f"Unknown special tool: {action.tool}",
                success=False,
                error=Exception(f"Special tool '{action.tool}' not found"),
                execution_time=time.time() - start_time
            )
        
        try:
            result = tool.run(**action.tool_input)
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=result,
                success=True,
                execution_time=time.time() - start_time,
                metadata={"special_tool": True}
            )
        except Exception as e:
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=None,
                success=False,
                error=e,
                execution_time=time.time() - start_time,
                metadata={"special_tool": True, "error": str(e)}
            )
    
    def _handle_missing_tool(self, action: AgentAction, start_time: float) -> AgentObservation:
        """Handle missing tool based on policy."""
        error_msg = f"Tool '{action.tool}' not found"
        available_tools = list(self.tools.keys())
        
        if self.on_missing_tool == ToolHandlingPolicy.ERROR.value:
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=None,
                success=False,
                error=Exception(error_msg),
                execution_time=time.time() - start_time,
                metadata={"available_tools": available_tools}
            )
            
        elif self.on_missing_tool == ToolHandlingPolicy.IGNORE.value:
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=f"Tool '{action.tool}' not available, skipping",
                success=False,
                execution_time=time.time() - start_time,
                metadata={"available_tools": available_tools, "ignored": True}
            )
            
        elif self.on_missing_tool == ToolHandlingPolicy.REFLECT.value:
            # Use special invalid tool for reflection
            reflection = self.special_tools[SpecialToolNames.INVALID_TOOL.value].run(
                tool_name=action.tool,
                available_tools=available_tools
            )
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output=reflection,
                success=False,
                execution_time=time.time() - start_time,
                metadata={"available_tools": available_tools, "reflection": True}
            )
        
        # Fallback to error
        return AgentObservation(
            action_id=action.id,
            tool=action.tool,
            output=None,
            success=False,
            error=Exception(error_msg),
            execution_time=time.time() - start_time
        )
    
    def _validate_arguments(self, action: AgentAction) -> Optional[str]:
        """
        Validate action arguments against tool schema.
        
        Args:
            action: Action to validate
            
        Returns:
            Error message if validation fails, None otherwise
        """
        tool = self.tools.get(action.tool)
        if not tool or not hasattr(tool, 'args_schema'):
            return None
        
        try:
            from global_utils.utils.util import validate_arguments
            validate_arguments(
                schema=tool.get_args_schema_json(),
                args=action.tool_input
            )
            return None
        except Exception as e:
            return f"Argument validation failed: {e}"
    
    def _action_to_chat_message(self, action: AgentAction) -> ChatMessage:
        """
        Convert AgentAction to ChatMessage with tool_calls.
        
        This allows us to reuse the existing ToolCapableMixin.invoke_tools logic.
        """
        tool_call = ToolCall(
            name=action.tool,
            args=action.tool_input,
            tool_call_id=action.id  # Use action ID as call ID
        )
        
        return ChatMessage(
            role=Role.ASSISTANT,
            content=action.reasoning or f"Using {action.tool}",
            tool_calls=[tool_call]
        )
    
    def _chat_messages_to_observation(
        self, 
        action: AgentAction, 
        result_messages: List[ChatMessage],
        start_time: float
    ) -> AgentObservation:
        """
        Convert ChatMessage results back to AgentObservation.
        
        The ToolCapableMixin.invoke_tools returns List[ChatMessage] with
        role=TOOL, so we need to convert this back to our observation format.
        """
        if not result_messages:
            return AgentObservation(
                action_id=action.id,
                tool=action.tool,
                output="No output from tool",
                success=False,
                error=Exception("Tool returned no results"),
                execution_time=time.time() - start_time
            )
        
        # Find the message corresponding to our action
        # ToolCapableMixin should return messages with tool_call_id matching action.id
        result_message = None
        for msg in result_messages:
            if (hasattr(msg, 'tool_call_id') and 
                msg.tool_call_id == action.id):
                result_message = msg
                break
        
        if not result_message:
            # Fallback to first message if no ID match
            result_message = result_messages[0]
        
        # Extract success/error from message content
        success = True
        error = None
        output = result_message.content
        
        # Check if content indicates an error
        if result_message.content and "Error:" in result_message.content:
            success = False
            error = Exception(result_message.content)
        
        return AgentObservation(
            action_id=action.id,
            tool=action.tool,
            output=output,
            success=success,
            error=error,
            execution_time=time.time() - start_time,
            metadata={
                "tool_message_id": getattr(result_message, 'tool_call_id', None),
                "message_count": len(result_messages)
            }
        )
    
    def _add_built_in_special_tools(self):
        """Add built-in special tools for error handling."""
        
        class ParseErrorTool(BaseTool):
            """Tool for handling parse errors with reflection."""
            name = SpecialToolNames.PARSE_ERROR.value
            description = "Reflect on parsing error and provide guidance"
            
            def run(self, error: str, raw_output: str, recoverable: bool = True) -> str:
                return (
                    f"I encountered a parsing error: {error}\n"
                    f"My previous output was: {raw_output}\n"
                    f"I should provide a clearer response with proper formatting. "
                    f"Let me think about what went wrong and try again."
                )
        
        class InvalidToolTool(BaseTool):
            """Tool for handling invalid tool requests."""
            name = SpecialToolNames.INVALID_TOOL.value
            description = "Handle requests for non-existent tools"
            
            def run(self, tool_name: str, available_tools: List[str]) -> str:
                return (
                    f"I tried to use '{tool_name}' but it's not available.\n"
                    f"Available tools are: {', '.join(available_tools)}\n"
                    f"Let me choose an appropriate tool from the available ones."
                )
        
        class FormatErrorTool(BaseTool):
            """Tool for handling format errors in custom parsers."""
            name = SpecialToolNames.FORMAT_ERROR.value
            description = "Handle output format errors"
            
            def run(self, error: str, expected_format: str, raw_output: str) -> str:
                return (
                    f"I made a formatting error: {error}\n"
                    f"Expected format: {expected_format}\n"
                    f"My output was: {raw_output}\n"
                    f"I'll follow the correct format in my next response."
                )
        
        # Add to special tools registry
        self.special_tools.update({
            SpecialToolNames.PARSE_ERROR.value: ParseErrorTool(),
            SpecialToolNames.INVALID_TOOL.value: InvalidToolTool(), 
            SpecialToolNames.FORMAT_ERROR.value: FormatErrorTool()
        })


class ToolValidator(SupportsToolValidation):
    """
    Validates agent actions before execution.
    
    Provides policy enforcement, permission checking, and safety validations
    before actions are executed. Can be used to implement organizational
    policies, rate limiting, security restrictions, etc.
    """
    
    def __init__(
        self,
        tools: Dict[str, BaseTool],
        *,
        allowed_tools: Optional[List[str]] = None,
        forbidden_tools: Optional[List[str]] = None,
        max_actions_per_minute: Optional[int] = None
    ):
        """
        Initialize tool validator.
        
        Args:
            tools: Available tools dictionary
            allowed_tools: Whitelist of allowed tool names (None = all allowed)
            forbidden_tools: Blacklist of forbidden tool names
            max_actions_per_minute: Rate limit for tool usage
        """
        self.tools = tools
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        self.forbidden_tools = set(forbidden_tools) if forbidden_tools else set()
        self.max_actions_per_minute = max_actions_per_minute
        
        # Rate limiting state
        self._action_timestamps: List[float] = []
    
    def validate_action(self, action: AgentAction) -> Tuple[bool, str]:
        """
        Validate if an action can be executed.
        
        Checks:
        - Tool exists
        - Tool is allowed (whitelist)
        - Tool is not forbidden (blacklist)  
        - Rate limits not exceeded
        - Custom validation rules
        
        Args:
            action: Action to validate
            
        Returns:
            (is_valid, error_message) tuple
        """
        # Check if tool exists (allow special tools)
        if not action.tool.startswith("_") and action.tool not in self.tools:
            return False, f"Unknown tool: {action.tool}"
        
        # Check whitelist
        if self.allowed_tools and action.tool not in self.allowed_tools:
            return False, f"Tool '{action.tool}' not in allowed list: {list(self.allowed_tools)}"
        
        # Check blacklist  
        if action.tool in self.forbidden_tools:
            return False, f"Tool '{action.tool}' is forbidden"
        
        # Check rate limits
        if self.max_actions_per_minute:
            current_time = time.time()
            # Clean old timestamps
            cutoff_time = current_time - 60  # 1 minute ago
            self._action_timestamps = [
                ts for ts in self._action_timestamps if ts > cutoff_time
            ]
            
            if len(self._action_timestamps) >= self.max_actions_per_minute:
                return False, f"Rate limit exceeded: {self.max_actions_per_minute} actions/minute"
            
            # Add current timestamp
            self._action_timestamps.append(current_time)
        
        # Additional custom validations could go here
        # - Check tool permissions based on user/context
        # - Validate dangerous operations
        # - Check resource usage limits
        # - Etc.
        
        return True, ""
