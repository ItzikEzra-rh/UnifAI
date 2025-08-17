"""
Example usage of the Engentic Workload Management System.

Shows how to use the SOLID workload interface and implementations
for hierarchical orchestration and shared context management.
"""

from elements.nodes.common.base_node import BaseNode
from elements.nodes.common.capabilities.iem_capable import IEMCapableMixin
from elements.nodes.common.capabilities.workload_capable import WorkloadCapableMixin
from graph.state.state_view import StateView
from graph.state.graph_state import Channel
from typing import ClassVar
from .interfaces import IWorkloadService
from .in_memory_service import InMemoryWorkloadService
from .state_bound_service import StateBoundWorkloadService
from .task import Task


class WorkloadExampleNode(WorkloadCapableMixin, IEMCapableMixin, BaseNode):
    """
    Example node showing SOLID workload management usage.
    
    Demonstrates:
    1. Using the IWorkloadService interface
    2. Different service implementations
    3. Hierarchical orchestration patterns
    4. Integration with existing systems
    """
    
    # Channel permissions (inherited from mixins)
    READS: ClassVar[set[str]] = {Channel.USER_PROMPT}
    WRITES: ClassVar[set[str]] = {Channel.MESSAGES}
    
    def run(self, state: StateView) -> StateView:
        """Example workflow using workload management."""
        prompt = state.get(Channel.USER_PROMPT, "")
        
        if not prompt.strip():
            return state
        
        # Example 1: Using state-bound service (default via mixin)
        self._example_state_bound_service(prompt)
        
        # Example 2: Using in-memory service directly
        self._example_in_memory_service(prompt)
        
        # Example 3: Service abstraction benefits
        self._example_service_abstraction(prompt)
        
        return state
    
    def _example_state_bound_service(self, prompt: str) -> None:
        """Example 1: Using StateBoundWorkloadService via mixin."""
        print("=== Example 1: State-Bound Service (via Mixin) ===")
        
        # The mixin automatically provides StateBoundWorkloadService
        # integrated with GraphState
        thread = self.create_thread(
            title="State-Bound Processing",
            objective="Process using GraphState integration"
        )
        
        print(f"Created thread: {thread.thread_id}")
        
        # Add context using mixin helpers
        self.add_fact_to_workspace(thread.thread_id, f"Query: {prompt}")
        self.set_workspace_variable(thread.thread_id, "service_type", "state_bound")
        
        # The workspace is automatically saved to GraphState
        context = self.get_thread_context(thread.thread_id)
        print(f"Context saved to GraphState: {bool(context)}")
    
    def _example_in_memory_service(self, prompt: str) -> None:
        """Example 2: Using InMemoryWorkloadService directly."""
        print("\n=== Example 2: In-Memory Service (Direct) ===")
        
        # Create an in-memory service directly
        in_memory_service: IWorkloadService = InMemoryWorkloadService()
        
        # Use the service interface
        thread = in_memory_service.create_thread(
            title="In-Memory Processing",
            objective="Process using in-memory storage",
            initiator=self.uid
        )
        
        print(f"Created thread: {thread.thread_id}")
        
        # Add context using service interface
        in_memory_service.add_fact(thread.thread_id, f"Query: {prompt}")
        in_memory_service.set_variable(thread.thread_id, "service_type", "in_memory")
        
        # Get workspace directly
        workspace = in_memory_service.get_workspace(thread.thread_id)
        print(f"Workspace facts: {len(workspace.facts)}")
        print(f"Workspace variables: {len(workspace.variables)}")
        
        # Get statistics
        stats = in_memory_service.get_statistics()
        print(f"Service statistics: {stats}")
    
    def _example_service_abstraction(self, prompt: str) -> None:
        """Example 3: Benefits of service abstraction."""
        print("\n=== Example 3: Service Abstraction Benefits ===")
        
        # Both services implement the same interface
        services = [
            ("StateBound", self.get_workload_service()),  # From mixin
            ("InMemory", InMemoryWorkloadService())       # Direct instance
        ]
        
        for service_name, service in services:
            print(f"\n--- Using {service_name} Service ---")
            
            # Same interface, different implementations
            thread = service.create_thread(
                title=f"{service_name} Thread",
                objective=f"Test {service_name} implementation",
                initiator=self.uid
            )
            
            # Same operations across implementations
            service.add_fact(thread.thread_id, f"Service: {service_name}")
            service.set_variable(thread.thread_id, "implementation", service_name.lower())
            
            # Same result structure
            context = service.get_context(thread.thread_id)
            print(f"Thread: {context['thread']['title']}")
            print(f"Facts: {len(context['workspace']['facts'])}")
            print(f"Variables: {len(context['workspace']['variables'])}")
    
    def _example_dependency_injection(self, service: IWorkloadService, prompt: str) -> None:
        """Example 4: Dependency injection pattern."""
        print("\n=== Example 4: Dependency Injection ===")
        
        # This method accepts any IWorkloadService implementation
        # Perfect for testing, different environments, etc.
        
        thread = service.create_thread(
            title="Injected Service Example",
            objective="Show dependency injection benefits",
            initiator=self.uid
        )
        
        # Work with the abstraction
        service.add_fact(thread.thread_id, f"Query: {prompt}")
        service.add_fact(thread.thread_id, "Processed via dependency injection")
        
        workspace = service.get_workspace(thread.thread_id)
        print(f"Facts added: {len(workspace.facts)}")
        
        return thread.thread_id


class ConfigurableWorkloadNode(BaseNode):
    """
    Example node that accepts workload service via dependency injection.
    
    Demonstrates clean separation of concerns and testability.
    """
    
    def __init__(self, workload_service: IWorkloadService, **kwargs):
        super().__init__(**kwargs)
        self._workload_service = workload_service
    
    def run(self, state: StateView) -> StateView:
        """Process using injected workload service."""
        prompt = state.get(Channel.USER_PROMPT, "")
        
        if not prompt.strip():
            return state
        
        # Use the injected service
        thread = self._workload_service.create_thread(
            title="Configurable Processing",
            objective="Process with configurable service",
            initiator=self.uid
        )
        
        # Process the prompt
        self._workload_service.add_fact(thread.thread_id, f"Input: {prompt}")
        self._workload_service.set_variable(thread.thread_id, "processor", self.uid)
        
        # Add result
        from .models import AgentResult
        result = AgentResult(
            content=f"Processed: {prompt}",
            artifacts={"thread_id": thread.thread_id},
            metrics={"processing_node": self.uid}
        )
        self._workload_service.add_result(thread.thread_id, result)
        
        print(f"Processed with configurable service: {thread.thread_id}")
        
        return state


# Example factory for different service types
class WorkloadServiceFactory:
    """Factory for creating workload service instances."""
    
    @staticmethod
    def create_service(service_type: str, **kwargs) -> IWorkloadService:
        """
        Create a workload service instance.
        
        Args:
            service_type: Type of service ("in_memory", "state_bound")
            **kwargs: Additional arguments for service creation
            
        Returns:
            IWorkloadService implementation
        """
        if service_type == "in_memory":
            return InMemoryWorkloadService()
        elif service_type == "state_bound":
            state = kwargs.get("state")
            if not state:
                raise ValueError("StateBoundWorkloadService requires 'state' parameter")
            return StateBoundWorkloadService(state)
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    @staticmethod
    def create_for_environment(env: str, **kwargs) -> IWorkloadService:
        """
        Create service based on environment.
        
        Args:
            env: Environment ("development", "production", "testing")
            **kwargs: Additional arguments
            
        Returns:
            Appropriate IWorkloadService implementation
        """
        if env in ["development", "testing"]:
            return InMemoryWorkloadService()  # Fast, isolated
        elif env == "production":
            state = kwargs.get("state")
            if state:
                return StateBoundWorkloadService(state)  # Persistent
            else:
                return InMemoryWorkloadService()  # Fallback
        else:
            raise ValueError(f"Unknown environment: {env}")


# Usage examples
def example_usage():
    """Show various usage patterns."""
    
    # 1. Direct instantiation
    in_memory = InMemoryWorkloadService()
    
    # 2. Factory creation
    service = WorkloadServiceFactory.create_service("in_memory")
    
    # 3. Environment-based creation
    dev_service = WorkloadServiceFactory.create_for_environment("development")
    
    # 4. All implement the same interface
    services = [in_memory, service, dev_service]
    
    for i, svc in enumerate(services):
        thread = svc.create_thread(f"Test {i}", "Test thread", "test_node")
        print(f"Service {i} created thread: {thread.thread_id}")
    
    print("All services work identically through IWorkloadService interface!")


if __name__ == "__main__":
    example_usage()