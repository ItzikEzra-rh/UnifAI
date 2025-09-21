"""
Integration tests for complete orchestrator workflows.

Tests end-to-end orchestration scenarios including simple and complex
cases, normal flows, and edge cases to ensure production-level quality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any
import json
from datetime import datetime

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind, WorkPlanService,
    Task, Workspace, WorkspaceContext
)
from elements.nodes.common.agent.constants import ExecutionPhase
from elements.tools.common.base_tool import BaseTool
from graph.state.state_view import StateView


class MockLLM:
    """Mock LLM for testing."""
    
    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["Mock LLM response"]
        self.call_count = 0
        self.last_messages = None
        self.last_tools = None
    
    def chat(self, messages, tools=None, **kwargs):
        """Mock chat method."""
        self.call_count += 1
        self.last_messages = messages
        self.last_tools = tools
        
        response_idx = min(self.call_count - 1, len(self.responses) - 1)
        return Mock(content=self.responses[response_idx])


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, responses: Dict[str, Any] = None):
        self.name = name
        self.description = f"Mock {name} tool"
        self.args_schema = None
        self.responses = responses or {}
        self.call_count = 0
        self.last_args = None
    
    def run(self, **kwargs):
        """Mock run method."""
        self.call_count += 1
        self.last_args = kwargs
        
        # Return configured response or default
        if self.name in self.responses:
            return self.responses[self.name]
        
        return {
            "success": True,
            "result": f"Mock result from {self.name}",
            "tool_used": self.name,
            "args": kwargs
        }


class TestOrchestratorSimpleScenarios:
    """Test simple orchestration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = MockLLM()
        self.mock_tools = [
            MockTool("domain_tool_1"),
            MockTool("domain_tool_2")
        ]
        
        # Mock state view
        self.mock_state = Mock(spec=StateView)
        
        # Create orchestrator
        self.orchestrator = OrchestratorNode(
            llm=self.mock_llm,
            tools=self.mock_tools,
            system_message="I specialize in data analysis",
            max_rounds=5
        )
        
        # Mock workspace and thread creation
        self.mock_workspace = Mock(spec=Workspace)
        self.mock_workspace.thread_id = "test-thread-123"
        
        self.orchestrator.get_workspace = Mock(return_value=self.mock_workspace)
        self.orchestrator.create_thread = Mock(return_value=Mock(thread_id="test-thread-123"))
        self.orchestrator.add_fact_to_workspace = Mock()
        self.orchestrator.set_workspace_variable = Mock()
        self.orchestrator.copy_graphstate_messages_to_workspace = Mock()
        self.orchestrator.get_adjacent_nodes = Mock(return_value=["data_analyst", "report_generator"])
    
    def test_simple_new_task_workflow(self):
        """Test simple workflow with new task."""
        # Create new task
        task = Task.create(
            content="Analyze Q4 sales data and create summary report",
            thread_id=None,  # New task
            created_by="user_node"
        )
        
        # Mock packet
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "packet-123"
        
        # Mock inbox to return our packet
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock strategy execution
        with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
            mock_strategy = Mock()
            mock_strategy.step.return_value = Mock(is_complete=True)
            mock_create_strategy.return_value = mock_strategy
            
            # Mock agent execution
            with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                mock_execute.return_value = Mock(
                    is_complete=True,
                    final_result="Analysis complete"
                )
                
                # Run orchestrator
                result_state = self.orchestrator.run(self.mock_state)
                
                # Verify workflow
                assert result_state == self.mock_state
                
                # Verify task was processed
                mock_packet.extract_task.assert_called_once()
                self.orchestrator.acknowledge.assert_called_once_with("packet-123")
                
                # Verify thread was created
                self.orchestrator.create_thread.assert_called_once()
                
                # Verify workspace setup
                self.orchestrator.add_fact_to_workspace.assert_called()
                self.orchestrator.set_workspace_variable.assert_called()
                
                # Verify orchestration cycle was run
                mock_create_strategy.assert_called_once()
                mock_execute.assert_called_once()
    
    def test_simple_response_handling(self):
        """Test simple response handling workflow."""
        # Create response task
        task = Task.create(
            content="Analysis results: Q4 sales increased 15%",
            thread_id="existing-thread",
            created_by="data_analyst",
            correlation_task_id="task-456"
        )
        task.result = {"analysis": "Q4 sales up 15%", "confidence": 0.95}
        task._is_response = True
        
        # Mock packet
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "response-packet-123"
        
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock workspace service for response ingestion
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.return_value = Mock(is_complete=False)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, '_run_orchestration_cycle') as mock_cycle:
                # Run orchestrator
                result_state = self.orchestrator.run(self.mock_state)
                
                # Verify response was processed
                mock_service.ingest_task_response.assert_called_once_with(
                    owner_uid=self.orchestrator.uid,
                    correlation_task_id="task-456",
                    result=task.result
                )
                
                # Verify orchestration cycle was triggered
                mock_cycle.assert_called_once_with(
                    "existing-thread",
                    "Continuing after batch response processing"
                )
    
    def test_empty_inbox_workflow(self):
        """Test workflow with empty inbox."""
        # Empty inbox
        self.orchestrator.inbox_packets = Mock(return_value=[])
        
        # Run orchestrator
        result_state = self.orchestrator.run(self.mock_state)
        
        # Should return state unchanged
        assert result_state == self.mock_state
        
        # No processing should occur
        self.orchestrator.acknowledge.assert_not_called()


class TestOrchestratorComplexScenarios:
    """Test complex orchestration scenarios with dependencies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = MockLLM([
            "I'll create a work plan for this complex task",
            "I'll assign the first task to the data analyst",
            "I'll monitor the progress of delegated tasks",
            "I'll create the final summary"
        ])
        
        self.orchestrator = OrchestratorNode(
            llm=self.mock_llm,
            tools=[MockTool("analysis_tool")],
            system_message="I specialize in complex data workflows",
            max_rounds=10
        )
        
        # Mock dependencies
        self.mock_workspace = Mock(spec=Workspace)
        self.orchestrator.get_workspace = Mock(return_value=self.mock_workspace)
        self.orchestrator.create_thread = Mock(return_value=Mock(thread_id="complex-thread"))
        self.orchestrator.add_fact_to_workspace = Mock()
        self.orchestrator.set_workspace_variable = Mock()
        self.orchestrator.copy_graphstate_messages_to_workspace = Mock()
        self.orchestrator.get_adjacent_nodes = Mock(return_value=[
            "data_extractor", "data_analyst", "report_generator", "chart_creator"
        ])
    
    def test_complex_dependency_chain_workflow(self):
        """Test complex workflow with dependency chain."""
        # Create complex task
        task = Task.create(
            content="Create comprehensive Q4 business report with data extraction, analysis, charts, and executive summary",
            thread_id=None,
            created_by="executive_node"
        )
        
        # Mock the complete workflow
        mock_packets = [Mock()]
        mock_packets[0].extract_task.return_value = task
        mock_packets[0].id = "complex-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=mock_packets)
        self.orchestrator.acknowledge = Mock()
        
        # Mock work plan service with complex plan
        mock_service = Mock(spec=WorkPlanService)
        
        # Create complex work plan with dependencies
        complex_plan = WorkPlan(
            summary="Q4 Business Report Generation",
            owner_uid=self.orchestrator.uid,
            thread_id="complex-thread",
            items={
                "extract_data": WorkItem(
                    id="extract_data",
                    title="Extract Q4 Data",
                    description="Extract raw Q4 data from databases",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.REMOTE,
                    dependencies=[]
                ),
                "analyze_data": WorkItem(
                    id="analyze_data", 
                    title="Analyze Q4 Data",
                    description="Perform statistical analysis on Q4 data",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.REMOTE,
                    dependencies=["extract_data"]
                ),
                "create_charts": WorkItem(
                    id="create_charts",
                    title="Create Charts",
                    description="Generate charts and visualizations",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.REMOTE,
                    dependencies=["analyze_data"]
                ),
                "generate_report": WorkItem(
                    id="generate_report",
                    title="Generate Executive Report",
                    description="Create final executive summary report",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.REMOTE,
                    dependencies=["analyze_data", "create_charts"]
                )
            }
        )
        
        mock_service.load.return_value = complex_plan
        mock_service.get_status_summary.return_value = Mock(
            exists=True,
            total_items=4,
            pending_items=4,
            is_complete=False
        )
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
                mock_strategy = Mock()
                mock_strategy.step.return_value = Mock(is_complete=False)
                mock_create_strategy.return_value = mock_strategy
                
                with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                    mock_execute.return_value = Mock(
                        is_complete=False,
                        final_result=None
                    )
                    
                    # Run orchestrator
                    result_state = self.orchestrator.run(self.mock_state)
                    
                    # Verify complex workflow was initiated
                    assert result_state == self.mock_state
                    
                    # Verify strategy was created with complex context
                    mock_create_strategy.assert_called_once()
                    create_args = mock_create_strategy.call_args
                    
                    # Should have orchestration tools
                    tools = create_args[1]['tools']
                    tool_names = [tool.name for tool in tools]
                    assert any('workplan' in name for name in tool_names)
                    assert any('delegate' in name for name in tool_names)
    
    def test_dependency_resolution_workflow(self):
        """Test workflow with dependency resolution."""
        # Simulate multiple response packets arriving
        response_packets = []
        
        # Response 1: Data extraction complete
        task1 = Task.create(
            content="Data extraction completed",
            thread_id="dep-thread",
            created_by="data_extractor",
            correlation_task_id="extract-task-123"
        )
        task1.result = {"records_extracted": 10000, "status": "success"}
        task1._is_response = True
        
        packet1 = Mock()
        packet1.extract_task.return_value = task1
        packet1.id = "response-1"
        response_packets.append(packet1)
        
        # Response 2: Data analysis complete
        task2 = Task.create(
            content="Data analysis completed",
            thread_id="dep-thread", 
            created_by="data_analyst",
            correlation_task_id="analyze-task-456"
        )
        task2.result = {"insights": ["Growth 15%", "Top product: Widget"], "status": "success"}
        task2._is_response = True
        
        packet2 = Mock()
        packet2.extract_task.return_value = task2
        packet2.id = "response-2"
        response_packets.append(packet2)
        
        self.orchestrator.inbox_packets = Mock(return_value=response_packets)
        self.orchestrator.acknowledge = Mock()
        
        # Mock service with dependency tracking
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        
        # Mock status showing progression
        mock_service.get_status_summary.side_effect = [
            Mock(is_complete=False, pending_items=2, done_items=1),  # After first response
            Mock(is_complete=False, pending_items=1, done_items=2)   # After second response
        ]
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, '_run_orchestration_cycle') as mock_cycle:
                # Run orchestrator
                result_state = self.orchestrator.run(self.mock_state)
                
                # Verify both responses were processed
                assert mock_service.ingest_task_response.call_count == 2
                
                # Verify responses were ingested correctly
                calls = mock_service.ingest_task_response.call_args_list
                assert calls[0][1]['correlation_task_id'] == "extract-task-123"
                assert calls[1][1]['correlation_task_id'] == "analyze-task-456"
                
                # Verify orchestration cycle was called for the thread
                mock_cycle.assert_called_with(
                    "dep-thread",
                    "Continuing after batch response processing"
                )
    
    def test_mixed_local_remote_workflow(self):
        """Test workflow with mixed local and remote execution."""
        # Create task requiring both local and remote work
        task = Task.create(
            content="Process data locally and generate remote report",
            thread_id=None,
            created_by="hybrid_requester"
        )
        
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "hybrid-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock work plan with mixed local/remote items
        mixed_plan = WorkPlan(
            summary="Mixed Local/Remote Processing",
            owner_uid=self.orchestrator.uid,
            thread_id="hybrid-thread",
            items={
                "local_preprocessing": WorkItem(
                    id="local_preprocessing",
                    title="Local Data Preprocessing",
                    description="Clean and prepare data locally",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.LOCAL,  # Local execution
                    dependencies=[]
                ),
                "remote_analysis": WorkItem(
                    id="remote_analysis",
                    title="Remote Analysis",
                    description="Perform complex analysis remotely",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.REMOTE,  # Remote execution
                    dependencies=["local_preprocessing"]
                ),
                "local_formatting": WorkItem(
                    id="local_formatting",
                    title="Local Report Formatting",
                    description="Format final report locally",
                    status=WorkItemStatus.PENDING,
                    kind=WorkItemKind.LOCAL,  # Local execution
                    dependencies=["remote_analysis"]
                )
            }
        )
        
        mock_service = Mock(spec=WorkPlanService)
        mock_service.load.return_value = mixed_plan
        mock_service.get_status_summary.return_value = Mock(
            exists=True,
            total_items=3,
            pending_items=1,  # local_preprocessing ready
            has_local_ready=True,
            is_complete=False
        )
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
                # Mock strategy to handle mixed execution
                mock_strategy = Mock()
                mock_strategy.get_current_phase.return_value = ExecutionPhase.EXECUTION
                mock_strategy.step.return_value = Mock(is_complete=False)
                mock_create_strategy.return_value = mock_strategy
                
                with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                    mock_execute.return_value = Mock(is_complete=False)
                    
                    # Run orchestrator
                    result_state = self.orchestrator.run(self.mock_state)
                    
                    # Verify mixed workflow was handled
                    assert result_state == self.mock_state
                    
                    # Verify strategy was created with appropriate tools
                    mock_create_strategy.assert_called_once()
                    create_args = mock_create_strategy.call_args
                    
                    # Should have both local execution and delegation tools
                    tools = create_args[1]['tools']
                    tool_names = [tool.name for tool in tools]
                    assert len(tools) > 1  # Should have multiple tool types


class TestOrchestratorErrorScenarios:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = MockLLM()
        self.orchestrator = OrchestratorNode(
            llm=self.mock_llm,
            tools=[MockTool("test_tool")],
            max_rounds=3
        )
        
        # Mock basic dependencies
        self.mock_workspace = Mock(spec=Workspace)
        self.orchestrator.get_workspace = Mock(return_value=self.mock_workspace)
        self.orchestrator.create_thread = Mock(return_value=Mock(thread_id="error-thread"))
        self.orchestrator.add_fact_to_workspace = Mock()
        self.orchestrator.set_workspace_variable = Mock()
        self.orchestrator.copy_graphstate_messages_to_workspace = Mock()
        self.orchestrator.get_adjacent_nodes = Mock(return_value=["worker_node"])
    
    def test_malformed_packet_handling(self):
        """Test handling of malformed packets."""
        # Create malformed packet
        malformed_packet = Mock()
        malformed_packet.extract_task.side_effect = Exception("Malformed packet")
        malformed_packet.id = "malformed-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=[malformed_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Should handle gracefully
        result_state = self.orchestrator.run(Mock(spec=StateView))
        
        # Should still acknowledge the packet
        self.orchestrator.acknowledge.assert_called_once_with("malformed-packet")
    
    def test_workspace_creation_failure(self):
        """Test handling of workspace creation failure."""
        # Create valid task
        task = Task.create(
            content="Test task",
            thread_id=None,
            created_by="test_node"
        )
        
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "test-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock workspace creation failure
        self.orchestrator.create_thread.side_effect = Exception("Workspace creation failed")
        
        # Should handle gracefully
        result_state = self.orchestrator.run(Mock(spec=StateView))
        
        # Should still acknowledge the packet
        self.orchestrator.acknowledge.assert_called_once_with("test-packet")
    
    def test_strategy_execution_failure(self):
        """Test handling of strategy execution failure."""
        task = Task.create(
            content="Test task",
            thread_id="existing-thread",
            created_by="test_node"
        )
        
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "strategy-fail-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock strategy creation failure
        with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
            mock_create_strategy.side_effect = Exception("Strategy creation failed")
            
            # Should handle gracefully
            result_state = self.orchestrator.run(Mock(spec=StateView))
            
            # Should still acknowledge the packet
            self.orchestrator.acknowledge.assert_called_once_with("strategy-fail-packet")
    
    def test_response_with_invalid_correlation(self):
        """Test handling of response with invalid correlation ID."""
        # Create response with invalid correlation
        task = Task.create(
            content="Invalid response",
            thread_id="test-thread",
            created_by="worker_node",
            correlation_task_id="nonexistent-correlation"
        )
        task.result = {"data": "some result"}
        task._is_response = True
        
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "invalid-response-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock service to return failure for invalid correlation
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = False  # Failed to ingest
        mock_service.get_status_summary.return_value = Mock(is_complete=False)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            # Should handle gracefully
            result_state = self.orchestrator.run(Mock(spec=StateView))
            
            # Should attempt to ingest response
            mock_service.ingest_task_response.assert_called_once_with(
                owner_uid=self.orchestrator.uid,
                correlation_task_id="nonexistent-correlation",
                result=task.result
            )
            
            # Should still acknowledge packet
            self.orchestrator.acknowledge.assert_called_once_with("invalid-response-packet")
    
    def test_llm_failure_during_execution(self):
        """Test handling of LLM failure during execution."""
        task = Task.create(
            content="Test task for LLM failure",
            thread_id=None,
            created_by="test_node"
        )
        
        mock_packet = Mock()
        mock_packet.extract_task.return_value = task
        mock_packet.id = "llm-fail-packet"
        
        self.orchestrator.inbox_packets = Mock(return_value=[mock_packet])
        self.orchestrator.acknowledge = Mock()
        
        # Mock LLM to fail
        failing_llm = Mock()
        failing_llm.chat.side_effect = Exception("LLM service unavailable")
        
        self.orchestrator.llm = failing_llm
        
        with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy
            
            with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                mock_execute.side_effect = Exception("Agent execution failed due to LLM")
                
                # Should handle gracefully
                result_state = self.orchestrator.run(Mock(spec=StateView))
                
                # Should still acknowledge packet
                self.orchestrator.acknowledge.assert_called_once_with("llm-fail-packet")
    
    def test_concurrent_packet_processing(self):
        """Test handling of multiple concurrent packets."""
        # Create multiple packets
        packets = []
        for i in range(5):
            task = Task.create(
                content=f"Concurrent task {i}",
                thread_id=f"thread-{i}",
                created_by="concurrent_node"
            )
            
            packet = Mock()
            packet.extract_task.return_value = task
            packet.id = f"concurrent-packet-{i}"
            packets.append(packet)
        
        self.orchestrator.inbox_packets = Mock(return_value=packets)
        self.orchestrator.acknowledge = Mock()
        
        # Mock service
        mock_service = Mock(spec=WorkPlanService)
        mock_service.get_status_summary.return_value = Mock(is_complete=True)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            # Should handle all packets
            result_state = self.orchestrator.run(Mock(spec=StateView))
            
            # Should acknowledge all packets
            assert self.orchestrator.acknowledge.call_count == 5
            
            # Verify all packet IDs were acknowledged
            acknowledged_ids = [call[0][0] for call in self.orchestrator.acknowledge.call_args_list]
            expected_ids = [f"concurrent-packet-{i}" for i in range(5)]
            assert set(acknowledged_ids) == set(expected_ids)


class TestOrchestratorBatchProcessing:
    """Test batch processing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = MockLLM()
        self.orchestrator = OrchestratorNode(
            llm=self.mock_llm,
            tools=[MockTool("batch_tool")],
            max_rounds=5
        )
        
        # Mock dependencies
        self.mock_workspace = Mock(spec=Workspace)
        self.orchestrator.get_workspace = Mock(return_value=self.mock_workspace)
        self.orchestrator.create_thread = Mock(return_value=Mock(thread_id="batch-thread"))
        self.orchestrator.add_fact_to_workspace = Mock()
        self.orchestrator.set_workspace_variable = Mock()
        self.orchestrator.copy_graphstate_messages_to_workspace = Mock()
        self.orchestrator.get_adjacent_nodes = Mock(return_value=["batch_worker"])
    
    def test_batch_response_processing(self):
        """Test batch processing of multiple responses."""
        # Create multiple response packets for same thread
        responses = []
        for i in range(3):
            task = Task.create(
                content=f"Response {i}",
                thread_id="batch-thread",
                created_by="batch_worker",
                correlation_task_id=f"task-{i}"
            )
            task.result = {"batch_result": f"result_{i}"}
            task._is_response = True
            
            packet = Mock()
            packet.extract_task.return_value = task
            packet.id = f"batch-response-{i}"
            responses.append(packet)
        
        self.orchestrator.inbox_packets = Mock(return_value=responses)
        self.orchestrator.acknowledge = Mock()
        
        # Mock service
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.return_value = Mock(is_complete=False)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, '_run_orchestration_cycle') as mock_cycle:
                # Run orchestrator
                result_state = self.orchestrator.run(Mock(spec=StateView))
                
                # Should process all responses
                assert mock_service.ingest_task_response.call_count == 3
                
                # Should run orchestration cycle only once per thread
                mock_cycle.assert_called_once_with(
                    "batch-thread",
                    "Continuing after batch response processing"
                )
                
                # Should acknowledge all packets
                assert self.orchestrator.acknowledge.call_count == 3
    
    def test_batch_processing_multiple_threads(self):
        """Test batch processing across multiple threads."""
        # Create responses for different threads
        responses = []
        threads = ["thread-A", "thread-B", "thread-C"]
        
        for i, thread_id in enumerate(threads):
            task = Task.create(
                content=f"Response for {thread_id}",
                thread_id=thread_id,
                created_by="multi_worker",
                correlation_task_id=f"task-{thread_id}"
            )
            task.result = {"thread_result": f"result_{thread_id}"}
            task._is_response = True
            
            packet = Mock()
            packet.extract_task.return_value = task
            packet.id = f"multi-response-{i}"
            responses.append(packet)
        
        self.orchestrator.inbox_packets = Mock(return_value=responses)
        self.orchestrator.acknowledge = Mock()
        
        # Mock service
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.return_value = Mock(is_complete=False)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, '_run_orchestration_cycle') as mock_cycle:
                # Run orchestrator
                result_state = self.orchestrator.run(Mock(spec=StateView))
                
                # Should process all responses
                assert mock_service.ingest_task_response.call_count == 3
                
                # Should run orchestration cycle once per thread
                assert mock_cycle.call_count == 3
                
                # Verify correct threads were processed
                cycle_calls = [call[0][0] for call in mock_cycle.call_args_list]
                assert set(cycle_calls) == set(threads)
    
    def test_batch_processing_efficiency(self):
        """Test that batch processing is more efficient than sequential."""
        # Create many response packets
        responses = []
        for i in range(10):
            task = Task.create(
                content=f"Efficiency test response {i}",
                thread_id="efficiency-thread",
                created_by="efficiency_worker",
                correlation_task_id=f"efficiency-task-{i}"
            )
            task.result = {"efficiency_result": f"result_{i}"}
            task._is_response = True
            
            packet = Mock()
            packet.extract_task.return_value = task
            packet.id = f"efficiency-response-{i}"
            responses.append(packet)
        
        self.orchestrator.inbox_packets = Mock(return_value=responses)
        self.orchestrator.acknowledge = Mock()
        
        # Mock service
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.return_value = Mock(is_complete=False)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, '_run_orchestration_cycle') as mock_cycle:
                # Run orchestrator
                result_state = self.orchestrator.run(Mock(spec=StateView))
                
                # Should process all 10 responses
                assert mock_service.ingest_task_response.call_count == 10
                
                # But should run orchestration cycle only ONCE (batch efficiency)
                mock_cycle.assert_called_once_with(
                    "efficiency-thread",
                    "Continuing after batch response processing"
                )
                
                # Should acknowledge all packets
                assert self.orchestrator.acknowledge.call_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

