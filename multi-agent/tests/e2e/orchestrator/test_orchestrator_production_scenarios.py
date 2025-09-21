"""
End-to-end production-level orchestrator scenario tests.

Tests realistic, complex scenarios that would occur in production
to ensure the orchestrator is truly production-ready.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime, timedelta

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.nodes.common.workload import (
    WorkPlan, WorkItem, WorkItemStatus, WorkItemKind, WorkPlanService,
    Task, Workspace, WorkspaceContext, ToolArguments, WorkItemResult
)
from elements.nodes.common.agent.constants import ExecutionPhase
from elements.tools.common.base_tool import BaseTool
from graph.state.state_view import StateView


class ProductionMockLLM:
    """Production-like mock LLM with realistic responses."""
    
    def __init__(self, scenario: str = "default"):
        self.scenario = scenario
        self.call_count = 0
        self.conversation_history = []
    
    def chat(self, messages, tools=None, **kwargs):
        """Mock chat with realistic responses based on scenario."""
        self.call_count += 1
        self.conversation_history.append({
            "messages": messages,
            "tools": [tool.name for tool in tools] if tools else [],
            "timestamp": datetime.now().isoformat()
        })
        
        # Return realistic responses based on scenario and phase
        if self.scenario == "data_analysis_pipeline":
            return self._data_analysis_responses(messages, tools)
        elif self.scenario == "document_processing":
            return self._document_processing_responses(messages, tools)
        elif self.scenario == "customer_report":
            return self._customer_report_responses(messages, tools)
        else:
            return Mock(content="Generic LLM response")
    
    def _data_analysis_responses(self, messages, tools):
        """Responses for data analysis pipeline scenario."""
        tool_names = [tool.name for tool in tools] if tools else []
        
        if "workplan.create_or_update" in tool_names and self.call_count == 1:
            # Planning phase - create work plan
            return Mock(
                content="I'll create a comprehensive data analysis pipeline",
                tool_calls=[{
                    "name": "workplan.create_or_update",
                    "args": {
                        "summary": "Q4 Sales Data Analysis Pipeline",
                        "items": [
                            {
                                "id": "extract_raw_data",
                                "title": "Extract Raw Sales Data",
                                "description": "Extract Q4 sales data from multiple databases",
                                "dependencies": [],
                                "kind": "remote",
                                "estimated_duration": "30 minutes"
                            },
                            {
                                "id": "clean_and_validate",
                                "title": "Clean and Validate Data",
                                "description": "Clean, validate, and normalize the extracted data",
                                "dependencies": ["extract_raw_data"],
                                "kind": "remote",
                                "estimated_duration": "45 minutes"
                            },
                            {
                                "id": "statistical_analysis",
                                "title": "Perform Statistical Analysis",
                                "description": "Run statistical analysis and identify trends",
                                "dependencies": ["clean_and_validate"],
                                "kind": "remote",
                                "estimated_duration": "1 hour"
                            },
                            {
                                "id": "generate_visualizations",
                                "title": "Generate Visualizations",
                                "description": "Create charts and graphs for the analysis",
                                "dependencies": ["statistical_analysis"],
                                "kind": "remote",
                                "estimated_duration": "30 minutes"
                            },
                            {
                                "id": "compile_final_report",
                                "title": "Compile Final Report",
                                "description": "Compile all analysis into executive summary",
                                "dependencies": ["statistical_analysis", "generate_visualizations"],
                                "kind": "local",
                                "estimated_duration": "20 minutes"
                            }
                        ]
                    }
                }]
            )
        elif "workplan.assign" in tool_names:
            # Allocation phase - assign work
            return Mock(
                content="I'll assign the ready tasks to appropriate nodes",
                tool_calls=[{
                    "name": "workplan.assign",
                    "args": {
                        "item_id": "extract_raw_data",
                        "kind": "remote",
                        "assigned_uid": "data_extractor_node",
                        "tool": "sql_extractor",
                        "args": {"tables": ["sales", "customers", "products"], "period": "Q4_2024"}
                    }
                }]
            )
        elif "iem.delegate_task" in tool_names:
            # Delegation
            return Mock(
                content="I'll delegate this task to the data extractor",
                tool_calls=[{
                    "name": "iem.delegate_task",
                    "args": {
                        "dst_uid": "data_extractor_node",
                        "content": "Extract Q4 sales data from all databases including sales, customers, and products tables. Ensure data integrity and include metadata about extraction process.",
                        "thread_id": "data_analysis_thread",
                        "parent_item_id": "extract_raw_data",
                        "should_respond": True,
                        "data": {"extraction_config": {"period": "Q4_2024", "format": "parquet"}}
                    }
                }]
            )
        elif "workplan.summarize" in tool_names:
            # Synthesis phase
            return Mock(
                content="Analysis pipeline completed successfully. All data has been extracted, cleaned, analyzed, and visualized. The final executive report shows Q4 sales increased by 15% with strong performance in the Widget Pro product line.",
                tool_calls=[{
                    "name": "workplan.summarize",
                    "args": {}
                }]
            )
        
        return Mock(content="Continuing with data analysis pipeline...")
    
    def _document_processing_responses(self, messages, tools):
        """Responses for document processing scenario."""
        # Similar realistic responses for document processing
        return Mock(content="Processing documents...")
    
    def _customer_report_responses(self, messages, tools):
        """Responses for customer report scenario."""
        # Similar realistic responses for customer reporting
        return Mock(content="Generating customer report...")


class ProductionMockTool(BaseTool):
    """Production-like mock tool with realistic behavior."""
    
    def __init__(self, name: str, success_rate: float = 0.95, latency_ms: int = 100):
        self.name = name
        self.description = f"Production mock {name}"
        self.args_schema = None
        self.success_rate = success_rate
        self.latency_ms = latency_ms
        self.call_count = 0
        self.call_history = []
    
    def run(self, **kwargs):
        """Mock run with realistic behavior."""
        self.call_count += 1
        
        # Simulate latency
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000.0)
        
        # Record call
        self.call_history.append({
            "timestamp": datetime.now().isoformat(),
            "args": kwargs
        })
        
        # Simulate occasional failures
        import random
        if random.random() > self.success_rate:
            return {
                "success": False,
                "error": f"Simulated failure in {self.name}",
                "retry_after": 5
            }
        
        # Return realistic success response
        return self._generate_realistic_response(kwargs)
    
    def _generate_realistic_response(self, args):
        """Generate realistic response based on tool name."""
        if "workplan.create_or_update" in self.name:
            return {
                "success": True,
                "plan_id": f"plan_{int(time.time())}",
                "total_items": len(args.get("items", [])),
                "status_counts": {"pending": len(args.get("items", [])), "done": 0}
            }
        elif "delegate" in self.name:
            return {
                "success": True,
                "task_id": f"task_{int(time.time())}",
                "packet_id": f"packet_{int(time.time())}",
                "dst_uid": args.get("dst_uid"),
                "correlation_info": {
                    "task_id": f"task_{int(time.time())}",
                    "parent_item_id": args.get("parent_item_id")
                }
            }
        else:
            return {
                "success": True,
                "result": f"Production result from {self.name}",
                "execution_time_ms": self.latency_ms,
                "metadata": {"tool": self.name, "args": args}
            }


class TestProductionDataAnalysisPipeline:
    """Test production-level data analysis pipeline scenario."""
    
    def setup_method(self):
        """Set up production-like test environment."""
        self.mock_llm = ProductionMockLLM("data_analysis_pipeline")
        
        # Create production-like tools
        self.production_tools = [
            ProductionMockTool("data_processor", success_rate=0.98, latency_ms=50),
            ProductionMockTool("chart_generator", success_rate=0.95, latency_ms=200),
            ProductionMockTool("report_compiler", success_rate=0.99, latency_ms=100)
        ]
        
        self.orchestrator = OrchestratorNode(
            llm=self.mock_llm,
            tools=self.production_tools,
            system_message="I specialize in comprehensive data analysis pipelines for business intelligence",
            max_rounds=15
        )
        
        # Mock production-like environment
        self._setup_production_environment()
    
    def _setup_production_environment(self):
        """Set up production-like environment mocks."""
        self.mock_workspace = Mock(spec=Workspace)
        self.mock_workspace.thread_id = "prod_data_analysis_thread"
        
        self.orchestrator.get_workspace = Mock(return_value=self.mock_workspace)
        self.orchestrator.create_thread = Mock(return_value=Mock(thread_id="prod_data_analysis_thread"))
        self.orchestrator.add_fact_to_workspace = Mock()
        self.orchestrator.set_workspace_variable = Mock()
        self.orchestrator.copy_graphstate_messages_to_workspace = Mock()
        
        # Mock realistic adjacent nodes
        self.orchestrator.get_adjacent_nodes = Mock(return_value=[
            "data_extractor_node",
            "data_cleaner_node", 
            "statistical_analyzer_node",
            "visualization_engine_node",
            "report_generator_node"
        ])
        
        # Mock realistic node cards
        def mock_get_node_card(uid):
            node_cards = {
                "data_extractor_node": {
                    "uid": "data_extractor_node",
                    "specialization": "High-performance SQL data extraction from multiple databases",
                    "capabilities": ["postgresql", "mysql", "mongodb", "data_validation"],
                    "max_concurrent_tasks": 5,
                    "avg_response_time": "2-5 minutes"
                },
                "statistical_analyzer_node": {
                    "uid": "statistical_analyzer_node", 
                    "specialization": "Advanced statistical analysis and machine learning",
                    "capabilities": ["regression", "clustering", "time_series", "forecasting"],
                    "max_concurrent_tasks": 3,
                    "avg_response_time": "5-15 minutes"
                },
                "visualization_engine_node": {
                    "uid": "visualization_engine_node",
                    "specialization": "Interactive charts, dashboards, and data visualizations",
                    "capabilities": ["plotly", "d3js", "tableau_integration", "real_time_charts"],
                    "max_concurrent_tasks": 8,
                    "avg_response_time": "1-3 minutes"
                }
            }
            return node_cards.get(uid, {"uid": uid, "specialization": "General purpose node"})
        
        self.orchestrator.get_node_card = Mock(side_effect=mock_get_node_card)
    
    def test_complete_data_analysis_pipeline(self):
        """Test complete end-to-end data analysis pipeline."""
        # Create realistic initial task
        initial_task = Task.create(
            content="Perform comprehensive Q4 2024 sales analysis including data extraction, cleaning, statistical analysis, visualization, and executive summary report",
            thread_id=None,
            created_by="business_intelligence_dashboard",
            data={
                "priority": "high",
                "deadline": "2024-12-15T17:00:00Z",
                "stakeholders": ["ceo", "sales_director", "finance_director"],
                "data_sources": ["sales_db", "crm_system", "inventory_db"]
            }
        )
        
        # Mock initial packet
        initial_packet = Mock()
        initial_packet.extract_task.return_value = initial_task
        initial_packet.id = "initial_analysis_request"
        
        # Simulate the complete workflow with realistic responses
        workflow_packets = [initial_packet]
        
        # Add realistic response packets that would arrive over time
        response_packets = self._create_realistic_response_sequence()
        workflow_packets.extend(response_packets)
        
        # Mock inbox to return packets in sequence
        packet_sequence = iter(workflow_packets)
        self.orchestrator.inbox_packets = Mock(side_effect=lambda: [next(packet_sequence, [])])
        self.orchestrator.acknowledge = Mock()
        
        # Mock work plan service with realistic behavior
        self._setup_realistic_work_plan_service()
        
        # Execute complete workflow
        workflow_results = []
        max_iterations = 10  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            try:
                with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
                    with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                        # Configure realistic strategy and agent behavior
                        self._configure_realistic_execution(mock_create_strategy, mock_execute, iteration)
                        
                        # Run one iteration
                        result_state = self.orchestrator.run(Mock(spec=StateView))
                        workflow_results.append({
                            "iteration": iteration,
                            "llm_calls": self.mock_llm.call_count,
                            "result": result_state
                        })
                        
                        # Check if workflow is complete
                        if self._is_workflow_complete(iteration):
                            break
                            
            except StopIteration:
                # No more packets
                break
        
        # Verify complete workflow execution
        self._verify_complete_workflow(workflow_results)
    
    def _create_realistic_response_sequence(self):
        """Create realistic sequence of response packets."""
        responses = []
        
        # Response 1: Data extraction complete
        extraction_task = Task.create(
            content="Data extraction completed successfully",
            thread_id="prod_data_analysis_thread",
            created_by="data_extractor_node",
            correlation_task_id="extract_task_001"
        )
        extraction_task.result = {
            "records_extracted": 125000,
            "tables_processed": ["sales", "customers", "products"],
            "data_quality_score": 0.94,
            "extraction_time": "4.2 minutes",
            "file_path": "/data/q4_2024_sales_raw.parquet",
            "metadata": {
                "row_count": 125000,
                "column_count": 23,
                "null_percentage": 0.06,
                "duplicate_percentage": 0.02
            }
        }
        extraction_task._is_response = True
        
        extraction_packet = Mock()
        extraction_packet.extract_task.return_value = extraction_task
        extraction_packet.id = "extraction_response"
        responses.append(extraction_packet)
        
        # Response 2: Data cleaning complete
        cleaning_task = Task.create(
            content="Data cleaning and validation completed",
            thread_id="prod_data_analysis_thread",
            created_by="data_cleaner_node",
            correlation_task_id="clean_task_002"
        )
        cleaning_task.result = {
            "records_cleaned": 122500,
            "records_removed": 2500,
            "validation_passed": True,
            "cleaning_time": "6.8 minutes",
            "file_path": "/data/q4_2024_sales_clean.parquet",
            "quality_improvements": {
                "null_percentage": 0.01,  # Improved from 0.06
                "duplicate_percentage": 0.00,  # Improved from 0.02
                "standardization_score": 0.98
            }
        }
        cleaning_task._is_response = True
        
        cleaning_packet = Mock()
        cleaning_packet.extract_task.return_value = cleaning_task
        cleaning_packet.id = "cleaning_response"
        responses.append(cleaning_packet)
        
        # Response 3: Statistical analysis complete
        analysis_task = Task.create(
            content="Statistical analysis completed with significant findings",
            thread_id="prod_data_analysis_thread",
            created_by="statistical_analyzer_node",
            correlation_task_id="analysis_task_003"
        )
        analysis_task.result = {
            "analysis_type": "comprehensive_sales_analysis",
            "key_findings": {
                "total_revenue": "$2,150,000",
                "revenue_growth": "15.3%",
                "top_performing_product": "Widget Pro",
                "seasonal_trends": "Strong Q4 performance",
                "customer_segments": {
                    "enterprise": {"revenue": "$1,290,000", "growth": "18.2%"},
                    "mid_market": {"revenue": "$645,000", "growth": "12.1%"},
                    "small_business": {"revenue": "$215,000", "growth": "8.7%"}
                }
            },
            "statistical_metrics": {
                "confidence_level": 0.95,
                "r_squared": 0.87,
                "p_value": 0.001,
                "sample_size": 122500
            },
            "analysis_time": "12.4 minutes",
            "model_accuracy": 0.91
        }
        analysis_task._is_response = True
        
        analysis_packet = Mock()
        analysis_packet.extract_task.return_value = analysis_task
        analysis_packet.id = "analysis_response"
        responses.append(analysis_packet)
        
        # Response 4: Visualization complete
        viz_task = Task.create(
            content="Data visualizations generated successfully",
            thread_id="prod_data_analysis_thread",
            created_by="visualization_engine_node",
            correlation_task_id="viz_task_004"
        )
        viz_task.result = {
            "visualizations_created": 8,
            "chart_types": ["revenue_trend", "product_performance", "customer_segments", "geographic_distribution"],
            "interactive_dashboard": "https://viz.company.com/q4_2024_sales",
            "static_exports": [
                "/reports/q4_revenue_trend.png",
                "/reports/q4_product_performance.png", 
                "/reports/q4_customer_segments.png"
            ],
            "generation_time": "3.1 minutes"
        }
        viz_task._is_response = True
        
        viz_packet = Mock()
        viz_packet.extract_task.return_value = viz_task
        viz_packet.id = "visualization_response"
        responses.append(viz_packet)
        
        return responses
    
    def _setup_realistic_work_plan_service(self):
        """Set up realistic work plan service behavior."""
        self.mock_service = Mock(spec=WorkPlanService)
        
        # Track work plan state progression
        self.work_plan_states = [
            # Initial state - no plan
            Mock(exists=False, total_items=0, is_complete=False),
            # After planning - plan created
            Mock(exists=True, total_items=5, pending_items=5, is_complete=False),
            # After first allocation - one item assigned
            Mock(exists=True, total_items=5, pending_items=4, waiting_items=1, is_complete=False),
            # After first response - one done, next ready
            Mock(exists=True, total_items=5, pending_items=3, waiting_items=1, done_items=1, is_complete=False),
            # Continue progression...
            Mock(exists=True, total_items=5, pending_items=0, waiting_items=2, done_items=3, is_complete=False),
            # Final state - all complete
            Mock(exists=True, total_items=5, pending_items=0, waiting_items=0, done_items=5, is_complete=True)
        ]
        
        self.state_index = 0
        
        def get_status_summary(owner_uid):
            if self.state_index < len(self.work_plan_states):
                state = self.work_plan_states[self.state_index]
                self.state_index += 1
                return state
            return self.work_plan_states[-1]  # Return final state
        
        self.mock_service.get_status_summary = Mock(side_effect=get_status_summary)
        self.mock_service.ingest_task_response.return_value = True
        self.mock_service.load.return_value = Mock()  # Mock work plan
        
        # Patch the service
        self.service_patcher = patch(
            'elements.nodes.orchestrator.orchestrator_node.WorkPlanService',
            return_value=self.mock_service
        )
        self.service_patcher.start()
    
    def _configure_realistic_execution(self, mock_create_strategy, mock_execute, iteration):
        """Configure realistic strategy and agent execution."""
        mock_strategy = Mock()
        
        # Configure strategy based on iteration (simulating phase progression)
        if iteration == 0:
            mock_strategy.get_current_phase.return_value = ExecutionPhase.PLANNING
        elif iteration < 4:
            mock_strategy.get_current_phase.return_value = ExecutionPhase.ALLOCATION
        elif iteration < 6:
            mock_strategy.get_current_phase.return_value = ExecutionPhase.MONITORING
        else:
            mock_strategy.get_current_phase.return_value = ExecutionPhase.SYNTHESIS
        
        mock_strategy.step.return_value = Mock(is_complete=(iteration > 6))
        mock_create_strategy.return_value = mock_strategy
        
        # Configure agent execution
        mock_execute.return_value = Mock(
            is_complete=(iteration > 6),
            final_result="Data analysis pipeline completed" if iteration > 6 else None
        )
    
    def _is_workflow_complete(self, iteration):
        """Check if workflow is complete."""
        return iteration > 6 or self.mock_llm.call_count > 10
    
    def _verify_complete_workflow(self, workflow_results):
        """Verify the complete workflow executed correctly."""
        assert len(workflow_results) > 0, "Workflow should have executed at least one iteration"
        
        # Verify LLM was called multiple times (realistic conversation)
        assert self.mock_llm.call_count >= 3, f"Expected multiple LLM calls, got {self.mock_llm.call_count}"
        
        # Verify conversation progression
        conversation = self.mock_llm.conversation_history
        assert len(conversation) >= 3, "Should have substantial conversation history"
        
        # Verify tools were used appropriately
        tool_usage = {}
        for conv in conversation:
            for tool_name in conv["tools"]:
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        # Should have used planning tools
        assert any("workplan" in tool for tool in tool_usage), "Should have used workplan tools"
        
        # Should have used delegation tools
        assert any("delegate" in tool for tool in tool_usage), "Should have used delegation tools"
        
        # Verify service interactions
        assert self.mock_service.get_status_summary.call_count >= 3, "Should have checked status multiple times"
        
        print(f"✅ Complete data analysis pipeline test passed:")
        print(f"   - LLM calls: {self.mock_llm.call_count}")
        print(f"   - Workflow iterations: {len(workflow_results)}")
        print(f"   - Tools used: {list(tool_usage.keys())}")
        print(f"   - Service calls: {self.mock_service.get_status_summary.call_count}")
    
    def teardown_method(self):
        """Clean up after test."""
        if hasattr(self, 'service_patcher'):
            self.service_patcher.stop()


class TestProductionErrorRecovery:
    """Test production-level error recovery scenarios."""
    
    def setup_method(self):
        """Set up error recovery test environment."""
        self.mock_llm = ProductionMockLLM("error_recovery")
        self.orchestrator = OrchestratorNode(
            llm=self.mock_llm,
            tools=[ProductionMockTool("unreliable_tool", success_rate=0.3)],  # Unreliable tool
            max_rounds=10
        )
        
        # Mock environment
        self.mock_workspace = Mock(spec=Workspace)
        self.orchestrator.get_workspace = Mock(return_value=self.mock_workspace)
        self.orchestrator.create_thread = Mock(return_value=Mock(thread_id="error_recovery_thread"))
        self.orchestrator.add_fact_to_workspace = Mock()
        self.orchestrator.set_workspace_variable = Mock()
        self.orchestrator.copy_graphstate_messages_to_workspace = Mock()
        self.orchestrator.get_adjacent_nodes = Mock(return_value=["unreliable_node", "backup_node"])
    
    def test_delegation_failure_recovery(self):
        """Test recovery from delegation failures."""
        # Create task that will experience delegation failures
        failing_task = Task.create(
            content="Task that will experience delegation failures",
            thread_id=None,
            created_by="test_requester"
        )
        
        # Create error response
        error_task = Task.create(
            content="Task failed due to node unavailability",
            thread_id="error_recovery_thread",
            created_by="unreliable_node",
            correlation_task_id="failing_task_001"
        )
        error_task.error = "Node temporarily unavailable - high load"
        error_task._is_response = True
        
        # Mock packets
        initial_packet = Mock()
        initial_packet.extract_task.return_value = failing_task
        initial_packet.id = "failing_initial"
        
        error_packet = Mock()
        error_packet.extract_task.return_value = error_task
        error_packet.id = "error_response"
        
        packets = [initial_packet, error_packet]
        packet_iter = iter(packets)
        
        self.orchestrator.inbox_packets = Mock(side_effect=lambda: [next(packet_iter, [])])
        self.orchestrator.acknowledge = Mock()
        
        # Mock service to handle error responses
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.side_effect = [
            Mock(exists=True, total_items=1, pending_items=1, is_complete=False),
            Mock(exists=True, total_items=1, failed_items=1, is_complete=True)  # Failed but complete
        ]
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
                with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                    mock_strategy = Mock()
                    mock_strategy.step.return_value = Mock(is_complete=True)
                    mock_create_strategy.return_value = mock_strategy
                    mock_execute.return_value = Mock(is_complete=True)
                    
                    # Run orchestrator - should handle error gracefully
                    for _ in range(2):  # Process both packets
                        try:
                            result_state = self.orchestrator.run(Mock(spec=StateView))
                        except StopIteration:
                            break
                    
                    # Verify error was ingested
                    mock_service.ingest_task_response.assert_called_with(
                        owner_uid=self.orchestrator.uid,
                        correlation_task_id="failing_task_001",
                        error="Node temporarily unavailable - high load"
                    )
    
    def test_partial_failure_handling(self):
        """Test handling of partial failures in complex workflows."""
        # Create complex task
        complex_task = Task.create(
            content="Complex multi-step task with potential partial failures",
            thread_id=None,
            created_by="complex_requester"
        )
        
        # Create mixed success/failure responses
        success_response = Task.create(
            content="Step 1 completed successfully",
            thread_id="error_recovery_thread",
            created_by="reliable_node",
            correlation_task_id="step_1_task"
        )
        success_response.result = {"step": 1, "status": "success", "data": "step1_data"}
        success_response._is_response = True
        
        failure_response = Task.create(
            content="Step 2 failed due to data corruption",
            thread_id="error_recovery_thread",
            created_by="unreliable_node",
            correlation_task_id="step_2_task"
        )
        failure_response.error = "Data corruption detected in input file"
        failure_response._is_response = True
        
        # Mock packets
        packets = [
            Mock(extract_task=Mock(return_value=complex_task), id="complex_initial"),
            Mock(extract_task=Mock(return_value=success_response), id="success_resp"),
            Mock(extract_task=Mock(return_value=failure_response), id="failure_resp")
        ]
        
        packet_iter = iter(packets)
        self.orchestrator.inbox_packets = Mock(side_effect=lambda: [next(packet_iter, [])])
        self.orchestrator.acknowledge = Mock()
        
        # Mock service for partial failure scenario
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.side_effect = [
            Mock(exists=True, total_items=3, pending_items=3, is_complete=False),
            Mock(exists=True, total_items=3, pending_items=2, done_items=1, is_complete=False),
            Mock(exists=True, total_items=3, pending_items=1, done_items=1, failed_items=1, is_complete=False)
        ]
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(self.orchestrator, 'create_strategy') as mock_create_strategy:
                with patch.object(self.orchestrator, 'execute_agent') as mock_execute:
                    mock_strategy = Mock()
                    mock_strategy.step.return_value = Mock(is_complete=False)
                    mock_create_strategy.return_value = mock_strategy
                    mock_execute.return_value = Mock(is_complete=False)
                    
                    # Process all packets
                    for _ in range(3):
                        try:
                            result_state = self.orchestrator.run(Mock(spec=StateView))
                        except StopIteration:
                            break
                    
                    # Verify both success and failure were handled
                    assert mock_service.ingest_task_response.call_count == 2
                    
                    # Verify orchestration continued despite partial failure
                    assert mock_create_strategy.call_count >= 2


class TestProductionPerformanceScenarios:
    """Test production-level performance scenarios."""
    
    def test_high_throughput_scenario(self):
        """Test orchestrator performance under high throughput."""
        mock_llm = ProductionMockLLM("high_throughput")
        orchestrator = OrchestratorNode(
            llm=mock_llm,
            tools=[ProductionMockTool("fast_tool", latency_ms=10)],
            max_rounds=5
        )
        
        # Mock environment
        mock_workspace = Mock(spec=Workspace)
        orchestrator.get_workspace = Mock(return_value=mock_workspace)
        orchestrator.create_thread = Mock(return_value=Mock(thread_id="perf_thread"))
        orchestrator.add_fact_to_workspace = Mock()
        orchestrator.set_workspace_variable = Mock()
        orchestrator.copy_graphstate_messages_to_workspace = Mock()
        orchestrator.get_adjacent_nodes = Mock(return_value=["fast_node"])
        orchestrator.acknowledge = Mock()
        
        # Create many concurrent packets
        num_packets = 50
        packets = []
        for i in range(num_packets):
            task = Task.create(
                content=f"High throughput task {i}",
                thread_id=f"perf_thread_{i % 5}",  # 5 different threads
                created_by="perf_tester",
                correlation_task_id=f"perf_task_{i}"
            )
            task.result = {"task_id": i, "result": f"result_{i}"}
            task._is_response = True
            
            packet = Mock()
            packet.extract_task.return_value = task
            packet.id = f"perf_packet_{i}"
            packets.append(packet)
        
        orchestrator.inbox_packets = Mock(return_value=packets)
        
        # Mock service for high throughput
        mock_service = Mock(spec=WorkPlanService)
        mock_service.ingest_task_response.return_value = True
        mock_service.get_status_summary.return_value = Mock(is_complete=False)
        
        with patch('elements.nodes.orchestrator.orchestrator_node.WorkPlanService', return_value=mock_service):
            with patch.object(orchestrator, '_run_orchestration_cycle') as mock_cycle:
                start_time = time.time()
                
                # Process all packets
                result_state = orchestrator.run(Mock(spec=StateView))
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Verify performance
                assert processing_time < 5.0, f"Processing {num_packets} packets took too long: {processing_time}s"
                
                # Verify all packets were processed
                assert orchestrator.acknowledge.call_count == num_packets
                
                # Verify batch efficiency (should not run cycle for each packet)
                assert mock_cycle.call_count <= 5, f"Too many orchestration cycles: {mock_cycle.call_count}"
                
                print(f"✅ High throughput test passed:")
                print(f"   - Processed {num_packets} packets in {processing_time:.2f}s")
                print(f"   - Average: {(processing_time/num_packets)*1000:.1f}ms per packet")
                print(f"   - Orchestration cycles: {mock_cycle.call_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print outputs

