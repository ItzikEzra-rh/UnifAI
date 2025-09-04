"""
Example: Integrating AgentCapableMixin with existing nodes.

This example shows how to enhance existing nodes with the new agent
capabilities while maintaining backward compatibility and demonstrating
different usage patterns.

Key Patterns Demonstrated:
1. Adding AgentCapableMixin to existing node
2. Simple automatic execution
3. Manual step-by-step control
4. Real-time streaming
5. Configuration customization
6. Error handling
"""

from typing import Optional, Any, List, Dict
from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.capabilities.llm_capable import LlmCapableMixin
from elements.nodes.common.capabilities.tool_capable import ToolCapableMixin
from elements.nodes.common.capabilities.workload_capable import WorkloadCapableMixin
from elements.nodes.common.capabilities.agent_capable import AgentCapableMixin
from elements.nodes.common.agent import AgentConfig

from elements.nodes.common.workload import Task, AgentResult
from elements.llms.common.chat.message import ChatMessage, Role
from graph.state.state_view import StateView

from elements.nodes.common.agent import ExecutionMode, StepType
from elements.nodes.common.agent.strategies import ReActStrategy
from elements.nodes.common.agent.execution import ToolValidator


class EnhancedCustomAgentNode(
    WorkloadCapableMixin,
    IEMCapableMixin,
    LlmCapableMixin,
    ToolCapableMixin,
    AgentCapableMixin,  # NEW: Add agent capabilities
    BaseNode
):
    """
    Enhanced CustomAgentNode with agent capabilities.
    
    Demonstrates how to add the AgentCapableMixin to existing nodes
    and use the different agent execution patterns.
    """
    
    def __init__(
        self,
        *,
        llm: Any,
        tools: List[Any] = None,
        system_message: str = "",
        max_rounds: Optional[int] = 15,
        use_agent_system: bool = True,  # NEW: Toggle between old/new system
        **kwargs: Any
    ):
        super().__init__(
            llm=llm,
            tools=tools or [],
            system_message=system_message,
            **kwargs
        )
        self.max_rounds = max_rounds
        self.use_agent_system = use_agent_system
    
    def run(self, state: StateView) -> StateView:
        """Main entry point - process all incoming TaskPackets."""
        # Initialize tools
        if self.tools:
            self._bind_tools(self.tools)
        
        # Process all incoming packets
        self.process_packets(state)
        return state
    
    def handle_task_packet(self, packet) -> None:
        """
        Process work using either old system or new agent system.
        
        This method demonstrates backward compatibility and the
        benefits of the new agent system.
        """
        try:
            task = packet.extract_task()
            task.mark_processed(self.uid)
            
            # Build conversation context (same for both approaches)
            conversation_context = self._build_conversation_context(task)
            
            if self.use_agent_system:
                # NEW APPROACH: Use agent system
                result = self._process_with_agent_system(task, conversation_context)
            else:
                # OLD APPROACH: Direct tool cycle (backward compatibility)
                result = self._process_with_legacy_system(task, conversation_context)
            
            # Create agent result (same for both)
            agent_result = self._create_agent_result(result)
            
            # Add to workspace and route response
            if task.thread_id:
                self._add_agent_result_to_workspace(task.thread_id, agent_result)
            
            self._route_response(task, agent_result, packet)
            
            print(f"CustomAgent {self.uid}: Processed task successfully")
            
        except Exception as e:
            print(f"CustomAgent {self.uid}: Error processing task: {e}")
    
    def _process_with_agent_system(self, task: Task, conversation_context: List[ChatMessage]) -> Dict[str, Any]:
        """
        NEW: Process using agent system with different patterns.
        
        Demonstrates various agent execution patterns and their benefits.
        """
        # Example 1: Simple automatic execution (most common)
        if task.data.get("mode") == "simple":
            return self._simple_agent_execution(conversation_context)
        
        # Example 2: Manual control for sensitive operations
        elif task.data.get("mode") == "manual":
            return self._manual_agent_execution(conversation_context)
        
        # Example 3: Streaming for real-time UI
        elif task.data.get("mode") == "streaming":
            return self._streaming_agent_execution(conversation_context)
        
        # Example 4: Custom configuration
        elif task.data.get("mode") == "custom":
            return self._custom_config_execution(conversation_context, task)
        
        # Default: Simple execution
        else:
            return self._simple_agent_execution(conversation_context)
    
    def _simple_agent_execution(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        Example 1: Simple automatic execution.
        
        This is the most straightforward way to use the agent system.
        Just call run_agent() and get the result.
        """
        config = AgentConfig(
            strategy="react",
            max_steps=self.max_rounds,
            execution_mode=ExecutionMode.AUTO,
            early_stopping="first_finish",
            return_intermediate=False
        )
        
        result = self.run_agent(messages, config=config)
        
        print(f"Agent completed in {result['execution_time']:.2f}s with {result['metadata']['total_steps']} steps")
        
        return result
    
    def _manual_agent_execution(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        Example 2: Manual control for sensitive operations.
        
        Use this when you need to inspect or approve each action
        before it's executed. Useful for high-stakes operations.
        """
        config = AgentConfig(
            strategy="react",
            max_steps=self.max_rounds,
            execution_mode=ExecutionMode.MANUAL,
            allowed_tools=["safe_tool", "calculator"],  # Only allow safe tools
            return_intermediate=True
        )
        
        iterator = self.create_agent_iterator(messages, config=config)
        
        results = []
        
        for step in iterator:
            if step.type == StepType.ACTION:
                action = step.data
                
                print(f"Agent wants to use: {action.tool} with {action.tool_input}")
                
                # Custom approval logic
                if self._should_approve_action(action):
                    # Execute the action ourselves
                    executor = self.create_tool_executor(config)
                    obs = executor.execute(action)
                    iterator.feed_observation(action, obs)
                    
                    print(f"Action result: {obs.content}")
                else:
                    # Reject the action
                    from agent.primitives import AgentObservation
                    obs = AgentObservation(
                        action_id=action.id,
                        tool=action.tool,
                        output="Action rejected by security policy",
                        success=False
                    )
                    iterator.feed_observation(action, obs)
                    
                    print("Action rejected by policy")
            
            elif step.type == StepType.FINISH:
                results.append(step.data.as_dict())
                break
        
        return results[0] if results else {"output": "No result", "success": False}
    
    def _streaming_agent_execution(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        Example 3: Streaming execution for real-time updates.
        
        Use this to provide real-time feedback to users or UIs.
        Each step is yielded as it happens.
        """
        config = AgentConfig(
            strategy="react",
            max_steps=self.max_rounds,
            execution_mode=ExecutionMode.AUTO
        )
        
        final_result = None
        
        print("Starting streaming execution...")
        
        for event in self.stream_agent(messages, config=config):
            if event["type"] == "agent_planning":
                print(f"🤔 Thinking: {event['data'].get('reasoning', '')[:100]}...")
                
            elif event["type"] == "agent_action":
                action_data = event["data"]
                print(f"🔧 Using {action_data['tool']} with {action_data['tool_input']}")
                
            elif event["type"] == "agent_observation":
                obs_data = event["data"]
                success_icon = "✅" if obs_data["success"] else "❌"
                print(f"{success_icon} Result: {str(obs_data['output'])[:100]}...")
                
            elif event["type"] == "agent_complete":
                final_result = event["data"]
                print(f"🎉 Completed: {final_result['output']}")
                break
                
            elif event["type"] == "agent_error":
                print(f"❌ Error: {event['data']['error']}")
                final_result = event["data"]
                break
        
        return final_result or {"output": "No result", "success": False}
    
    def _custom_config_execution(self, messages: List[ChatMessage], task: Task) -> Dict[str, Any]:
        """
        Example 4: Custom configuration based on task requirements.
        
        Demonstrates how to customize the agent behavior based on
        the specific task or context.
        """
        # Extract custom settings from task
        task_config = task.data.get("agent_config", {})
        
        # Create custom validator for this task
        def custom_action_filter(action):
            # Custom logic based on task requirements
            if task.data.get("high_security", False):
                dangerous_tools = ["file_delete", "system_command"]
                if action.tool in dangerous_tools:
                    return False
            return True
        
        # Build configuration
        config = AgentConfig(
            strategy=task_config.get("strategy", "react"),
            max_steps=task_config.get("max_steps", self.max_rounds),
            execution_mode=ExecutionMode.GUIDED if task.data.get("require_approval") else ExecutionMode.AUTO,
            allowed_tools=task_config.get("allowed_tools"),
            forbidden_tools=task_config.get("forbidden_tools", []),
            max_execution_time=task_config.get("timeout", 60.0),
            return_intermediate=task_config.get("detailed_logging", False)
        )
        
        # Create iterator with custom callback
        iterator = self.create_agent_iterator(
            messages, 
            config=config,
            on_action=custom_action_filter
        )
        
        # Execute with custom handling
        for step in iterator:
            if step.type == StepType.FINISH:
                return step.data.as_dict()
            elif step.type == StepType.ERROR:
                return {"output": f"Error: {step.data}", "success": False}
        
        return {"output": "Execution completed without result", "success": False}
    
    def _process_with_legacy_system(self, task: Task, conversation_context: List[ChatMessage]) -> str:
        """
        OLD: Legacy processing using _execute_tool_cycle.
        
        Kept for backward compatibility demonstration.
        """
        # Use the old tool cycle method
        assistant_response = self._execute_tool_cycle(
            conversation_context, 
            self._chat,
            self.max_rounds
        )
        
        return assistant_response.content
    
    def _should_approve_action(self, action) -> bool:
        """
        Custom approval logic for manual mode.
        
        In a real system, this might check:
        - User permissions
        - Security policies  
        - Resource limits
        - Approval workflows
        """
        # Example: Reject dangerous operations
        dangerous_tools = ["delete_file", "run_command", "send_email"]
        if action.tool in dangerous_tools:
            print(f"⚠️  Dangerous tool '{action.tool}' requires additional approval")
            return False
        
        # Example: Check resource usage
        if action.tool_input.get("size", 0) > 1000000:  # Large operations
            print(f"⚠️  Large operation detected, requires approval")
            return False
        
        return True
    
    def _build_conversation_context(self, task: Task) -> List[ChatMessage]:
        """
        Build conversation context (same as before).
        
        This method remains unchanged, showing that the existing
        context building logic is preserved.
        """
        messages = []
        
        # Add system message if configured
        if self.system_message:
            messages.append(ChatMessage(
                role=Role.SYSTEM, 
                content=self.system_message
            ))
        
        # Add task content
        messages.append(ChatMessage(
            role=Role.USER,
            content=task.content
        ))
        
        return messages
    
    def _create_agent_result(self, result: Any) -> AgentResult:
        """Create AgentResult from processing result (same as before)."""
        if isinstance(result, dict):
            output = result.get("output", str(result))
            reasoning = result.get("reasoning", "")
        else:
            output = str(result)
            reasoning = ""
        
        return AgentResult(
            agent_id=self.uid,
            output=output,
            reasoning=reasoning,
            metadata={
                "system_version": "enhanced_agent_system",
                "use_agent_system": self.use_agent_system
            }
        )


# Example usage patterns
def example_usage_patterns():
    """
    Demonstrate different ways to use the enhanced agent node.
    """
    # This would typically be created by your node factory
    # but shown here for illustration
    
    # Example 1: Simple replacement for existing node
    simple_config = {
        "mode": "simple"
    }
    
    # Example 2: Manual control for sensitive operations  
    sensitive_config = {
        "mode": "manual",
        "high_security": True,
        "require_approval": True
    }
    
    # Example 3: Streaming for real-time UI
    streaming_config = {
        "mode": "streaming"
    }
    
    # Example 4: Custom configuration per task
    custom_config = {
        "mode": "custom",
        "agent_config": {
            "strategy": "react",
            "max_steps": 20,
            "allowed_tools": ["calculator", "search", "summarize"],
            "timeout": 30.0,
            "detailed_logging": True
        }
    }
    
    print("Enhanced agent node supports multiple execution patterns:")
    print("1. Simple automatic execution")
    print("2. Manual control with approval")
    print("3. Real-time streaming")
    print("4. Custom configuration per task")
    print("5. Backward compatibility with legacy system")


if __name__ == "__main__":
    example_usage_patterns()
