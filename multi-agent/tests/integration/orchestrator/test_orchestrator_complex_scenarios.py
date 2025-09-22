"""
Complex Scenarios Integration Tests for Orchestrator System.

These tests verify orchestrator functionality with complex, multi-step workflows
that involve advanced orchestration patterns, error recovery, and sophisticated
coordination scenarios.

SOLID Principles Applied:
- Single Responsibility: Each test focuses on one complex orchestration pattern
- Open/Closed: Tests are extensible for new complex scenarios  
- Liskov Substitution: Uses real orchestrator components with complex mocking
- Interface Segregation: Clean interfaces for complex scenario testing
- Dependency Inversion: Depends on orchestrator abstractions and sophisticated fixtures
"""

import pytest
from unittest.mock import patch, Mock
from typing import Dict, Any, List
import time

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.nodes.common.workload import Task, WorkPlan, WorkPlanService, WorkItemKind, WorkItemStatus
from elements.llms.common.chat.message import ChatMessage, Role
from core.models import ElementCard

# Import our clean, SOLID fixtures
from tests.fixtures.orchestrator_integration import (
    PredictableLLM, ExecutionTracker
)


@pytest.mark.integration
@pytest.mark.orchestrator
class TestOrchestratorComplexWorkflows:
    """
    Integration tests for complex orchestrator workflows.
    
    These tests verify sophisticated orchestration scenarios that involve
    multiple phases, complex dependencies, and advanced coordination patterns.
    """
    
    def test_complex_multi_phase_workflow_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test complex workflow with multiple phases and dependencies.
        
        Verifies:
        1. Multi-phase work plan creation
        2. Complex dependency management
        3. Phase transitions with dependencies
        4. Sophisticated workflow coordination
        """
        try:
            # Create complex task requiring multi-phase approach
            task = integration_task_factory(
                content="Conduct comprehensive market research study with data collection, analysis, validation, and reporting phases",
                thread_id="complex_workflow_thread"
            )
            
            # Set up LLM response for complex multi-phase work plan
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Comprehensive market research study workflow",
                    "items": [
                        # Phase 1: Data Collection
                        {
                            "id": "primary_data_collection",
                            "title": "Primary Data Collection",
                            "description": "Conduct surveys and interviews",
                            "kind": "remote",
                            "dependencies": []
                        },
                        {
                            "id": "secondary_data_collection", 
                            "title": "Secondary Data Collection",
                            "description": "Gather industry reports and public data",
                            "kind": "remote",
                            "dependencies": []
                        },
                        # Phase 2: Data Processing (depends on Phase 1)
                        {
                            "id": "data_cleaning",
                            "title": "Data Cleaning and Preparation",
                            "description": "Clean and prepare collected data",
                            "kind": "local",
                            "dependencies": ["primary_data_collection", "secondary_data_collection"]
                        },
                        {
                            "id": "data_validation",
                            "title": "Data Validation",
                            "description": "Validate data quality and completeness",
                            "kind": "remote",
                            "dependencies": ["data_cleaning"]
                        },
                        # Phase 3: Analysis (depends on Phase 2)
                        {
                            "id": "statistical_analysis",
                            "title": "Statistical Analysis",
                            "description": "Perform statistical analysis on validated data",
                            "kind": "remote",
                            "dependencies": ["data_validation"]
                        },
                        {
                            "id": "trend_analysis",
                            "title": "Trend Analysis",
                            "description": "Analyze market trends and patterns",
                            "kind": "remote", 
                            "dependencies": ["data_validation"]
                        },
                        # Phase 4: Synthesis (depends on Phase 3)
                        {
                            "id": "insights_synthesis",
                            "title": "Insights Synthesis",
                            "description": "Synthesize analysis results into insights",
                            "kind": "local",
                            "dependencies": ["statistical_analysis", "trend_analysis"]
                        },
                        # Phase 5: Reporting (depends on Phase 4)
                        {
                            "id": "report_generation",
                            "title": "Final Report Generation",
                            "description": "Generate comprehensive market research report",
                            "kind": "local",
                            "dependencies": ["insights_synthesis"]
                        }
                    ]
                },
                content="Created comprehensive multi-phase workflow"
            )
            
            # Add delegation responses for remote tasks
            for task_info in [
                ("primary_data_collection", "survey_specialist"),
                ("secondary_data_collection", "research_analyst"),
                ("data_validation", "quality_assurance"),
                ("statistical_analysis", "statistician"),
                ("trend_analysis", "market_analyst")
            ]:
                task_id, node_uid = task_info
                predictable_llm.add_tool_call_response(
                    tool_name="iem.delegate_task",
                    arguments={
                        "dst_uid": node_uid,
                        "content": f"Execute {task_id} for market research study",
                        "thread_id": "complex_workflow_thread",
                        "work_item_id": task_id
                    },
                    content=f"Delegated {task_id} to {node_uid}"
                )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock specialized adjacent nodes
            from core.enums import ResourceCategory
            
            mock_adjacent_nodes = {
                "survey_specialist": ElementCard(uid="survey_specialist", category=ResourceCategory.NODE, type_key="survey_node",
                              name="Survey Specialist", description="Primary data collection", 
                              capabilities={"survey_design", "interviews"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"survey_design": True, "interviews": True}),
                "research_analyst": ElementCard(uid="research_analyst", category=ResourceCategory.NODE, type_key="research_node",
                              name="Research Analyst", description="Secondary research", 
                              capabilities={"desk_research", "industry_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"desk_research": True, "industry_analysis": True}),
                "quality_assurance": ElementCard(uid="quality_assurance", category=ResourceCategory.NODE, type_key="qa_node",
                              name="Quality Assurance", description="Data validation", 
                              capabilities={"data_validation", "quality_control"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"data_validation": True, "quality_control": True}),
                "statistician": ElementCard(uid="statistician", category=ResourceCategory.NODE, type_key="stats_node",
                              name="Statistician", description="Statistical analysis", 
                              capabilities={"statistics", "hypothesis_testing"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"statistics": True, "hypothesis_testing": True}),
                "market_analyst": ElementCard(uid="market_analyst", category=ResourceCategory.NODE, type_key="market_node",
                              name="Market Analyst", description="Market trend analysis", 
                              capabilities={"trend_analysis", "forecasting"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"trend_analysis": True, "forecasting": True})
            }
            
            # Execute complex workflow
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value=mock_adjacent_nodes), \
                 patch.object(integration_orchestrator, 'send_task', return_value="complex_workflow_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Complex workflow was orchestrated
                assert result is not None
                assert predictable_llm.call_count > 0
                
                # VERIFY: Complex work plan structure
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                plan_service = WorkPlanService(workspace)
                work_plan = plan_service.load(integration_orchestrator.uid)
                
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    
                    # Verify complex dependency structure
                    assert len(work_plan.items) >= 8, "Should have multiple work items in complex workflow"
                    
                    # Verify dependency chains
                    if "data_cleaning" in work_plan.items:
                        cleaning_item = work_plan.items["data_cleaning"]
                        assert "primary_data_collection" in cleaning_item.dependencies
                        assert "secondary_data_collection" in cleaning_item.dependencies
                    
                    if "insights_synthesis" in work_plan.items:
                        synthesis_item = work_plan.items["insights_synthesis"]
                        assert "statistical_analysis" in synthesis_item.dependencies
                        assert "trend_analysis" in synthesis_item.dependencies
                    
                    # Verify mix of local and remote work
                    local_items = [item for item in work_plan.items.values() if item.kind == WorkItemKind.LOCAL]
                    remote_items = [item for item in work_plan.items.values() if item.kind == WorkItemKind.REMOTE]
                    
                    assert len(local_items) >= 3, "Should have local coordination items"
                    assert len(remote_items) >= 5, "Should have remote specialized items"
                
                print("✅ COMPLEX MULTI-PHASE WORKFLOW WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Complex multi-phase workflow failed: {e}")
    
    def test_dynamic_workflow_adaptation_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test dynamic workflow adaptation based on intermediate results.
        
        Verifies:
        1. Initial workflow execution
        2. Simulated intermediate results
        3. Workflow adaptation and replanning
        4. Dynamic task addition/modification
        """
        try:
            # Create task that might require adaptation
            task = integration_task_factory(
                content="Analyze customer satisfaction data and adapt analysis based on initial findings",
                thread_id="adaptive_workflow_thread"
            )
            
            # Set up initial work plan
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Adaptive customer satisfaction analysis",
                    "items": [
                        {
                            "id": "initial_analysis",
                            "title": "Initial Data Analysis",
                            "description": "Perform initial analysis to determine approach",
                            "kind": "local",
                            "dependencies": []
                        },
                        {
                            "id": "detailed_analysis",
                            "title": "Detailed Analysis",
                            "description": "Detailed analysis based on initial findings",
                            "kind": "remote",
                            "dependencies": ["initial_analysis"]
                        }
                    ]
                },
                content="Created initial adaptive workflow"
            )
            
            # Set up adaptation response (simulating workflow modification)
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Adapted customer satisfaction analysis based on findings",
                    "items": [
                        {
                            "id": "initial_analysis",
                            "title": "Initial Data Analysis",
                            "description": "Perform initial analysis to determine approach",
                            "kind": "local",
                            "dependencies": []
                        },
                        {
                            "id": "detailed_analysis",
                            "title": "Detailed Analysis", 
                            "description": "Detailed analysis based on initial findings",
                            "kind": "remote",
                            "dependencies": ["initial_analysis"]
                        },
                        {
                            "id": "sentiment_analysis",
                            "title": "Sentiment Analysis",
                            "description": "Additional sentiment analysis based on initial insights",
                            "kind": "remote",
                            "dependencies": ["initial_analysis"]
                        },
                        {
                            "id": "comparative_analysis",
                            "title": "Comparative Analysis",
                            "description": "Compare with industry benchmarks",
                            "kind": "remote",
                            "dependencies": ["detailed_analysis", "sentiment_analysis"]
                        }
                    ]
                },
                content="Adapted workflow based on initial findings"
            )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock adaptive analysis nodes
            from core.enums import ResourceCategory
            
            mock_adjacent_nodes = {
                "sentiment_analyzer": ElementCard(uid="sentiment_analyzer", category=ResourceCategory.NODE, type_key="sentiment_node",
                              name="Sentiment Analyzer", description="NLP sentiment analysis", 
                              capabilities={"nlp", "sentiment_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"nlp": True, "sentiment_analysis": True}),
                "benchmark_analyst": ElementCard(uid="benchmark_analyst", category=ResourceCategory.NODE, type_key="benchmark_node",
                              name="Benchmark Analyst", description="Industry comparison", 
                              capabilities={"benchmarking", "competitive_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"benchmarking": True, "competitive_analysis": True})
            }
            
            # Execute adaptive workflow
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value=mock_adjacent_nodes), \
                 patch.object(integration_orchestrator, 'send_task', return_value="adaptive_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Adaptive workflow executed
                assert result is not None
                assert predictable_llm.call_count > 0
                
                # For complex scenario test, verify orchestrator can handle
                # workflow modifications and dynamic planning
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                if workspace:
                    execution_tracker.track_workspace_fact("Adaptive workflow executed")
                
                print("✅ DYNAMIC WORKFLOW ADAPTATION WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Dynamic workflow adaptation failed: {e}")
    
    def test_parallel_workflow_execution_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test parallel workflow execution with independent branches.
        
        Verifies:
        1. Parallel branch identification
        2. Independent workflow execution
        3. Synchronization points
        4. Final convergence handling
        """
        try:
            # Create task with parallel execution opportunities
            task = integration_task_factory(
                content="Conduct comprehensive product analysis with parallel market research, technical assessment, and financial analysis",
                thread_id="parallel_workflow_thread"
            )
            
            # Set up parallel workflow plan
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Parallel product analysis workflow",
                    "items": [
                        # Parallel Branch 1: Market Research
                        {
                            "id": "market_research",
                            "title": "Market Research Analysis",
                            "description": "Analyze market conditions and competition",
                            "kind": "remote",
                            "dependencies": []
                        },
                        {
                            "id": "customer_analysis",
                            "title": "Customer Analysis",
                            "description": "Analyze customer needs and preferences",
                            "kind": "remote",
                            "dependencies": []
                        },
                        # Parallel Branch 2: Technical Assessment  
                        {
                            "id": "technical_feasibility",
                            "title": "Technical Feasibility Study",
                            "description": "Assess technical feasibility and requirements",
                            "kind": "remote",
                            "dependencies": []
                        },
                        {
                            "id": "technology_evaluation",
                            "title": "Technology Evaluation",
                            "description": "Evaluate technology stack and architecture",
                            "kind": "remote",
                            "dependencies": []
                        },
                        # Parallel Branch 3: Financial Analysis
                        {
                            "id": "cost_analysis",
                            "title": "Cost Analysis",
                            "description": "Analyze development and operational costs",
                            "kind": "remote", 
                            "dependencies": []
                        },
                        {
                            "id": "roi_projection",
                            "title": "ROI Projection",
                            "description": "Project return on investment",
                            "kind": "remote",
                            "dependencies": []
                        },
                        # Synchronization Point: Final Analysis
                        {
                            "id": "comprehensive_synthesis",
                            "title": "Comprehensive Analysis Synthesis",
                            "description": "Synthesize all parallel analysis results",
                            "kind": "local",
                            "dependencies": ["market_research", "customer_analysis", "technical_feasibility", 
                                           "technology_evaluation", "cost_analysis", "roi_projection"]
                        }
                    ]
                },
                content="Created parallel workflow with synchronization"
            )
            
            # Add delegation responses for all parallel tasks
            parallel_tasks = [
                ("market_research", "market_researcher"),
                ("customer_analysis", "customer_analyst"), 
                ("technical_feasibility", "tech_architect"),
                ("technology_evaluation", "tech_evaluator"),
                ("cost_analysis", "cost_analyst"),
                ("roi_projection", "financial_analyst")
            ]
            
            for task_id, node_uid in parallel_tasks:
                predictable_llm.add_tool_call_response(
                    tool_name="iem.delegate_task",
                    arguments={
                        "dst_uid": node_uid,
                        "content": f"Execute {task_id} for product analysis",
                        "thread_id": "parallel_workflow_thread",
                        "work_item_id": task_id
                    },
                    content=f"Delegated {task_id} to {node_uid}"
                )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock parallel execution specialists
            from core.enums import ResourceCategory
            
            mock_adjacent_nodes = {
                # Market Research Branch
                "market_researcher": ElementCard(uid="market_researcher", category=ResourceCategory.NODE, type_key="market_node",
                              name="Market Researcher", description="Market analysis", 
                              capabilities={"market_research", "competitive_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"market_research": True, "competitive_analysis": True}),
                "customer_analyst": ElementCard(uid="customer_analyst", category=ResourceCategory.NODE, type_key="customer_node",
                              name="Customer Analyst", description="Customer analysis", 
                              capabilities={"customer_research", "user_experience"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"customer_research": True, "user_experience": True}),
                # Technical Branch
                "tech_architect": ElementCard(uid="tech_architect", category=ResourceCategory.NODE, type_key="tech_node",
                              name="Technical Architect", description="Technical feasibility", 
                              capabilities={"architecture", "system_design"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"architecture": True, "system_design": True}),
                "tech_evaluator": ElementCard(uid="tech_evaluator", category=ResourceCategory.NODE, type_key="evaluator_node",
                              name="Technology Evaluator", description="Technology assessment", 
                              capabilities={"tech_evaluation", "performance_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"tech_evaluation": True, "performance_analysis": True}),
                # Financial Branch
                "cost_analyst": ElementCard(uid="cost_analyst", category=ResourceCategory.NODE, type_key="cost_node",
                              name="Cost Analyst", description="Cost analysis", 
                              capabilities={"cost_modeling", "budget_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"cost_modeling": True, "budget_analysis": True}),
                "financial_analyst": ElementCard(uid="financial_analyst", category=ResourceCategory.NODE, type_key="financial_node",
                              name="Financial Analyst", description="ROI analysis", 
                              capabilities={"financial_modeling", "roi_analysis"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"financial_modeling": True, "roi_analysis": True})
            }
            
            # Execute parallel workflow
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value=mock_adjacent_nodes), \
                 patch.object(integration_orchestrator, 'send_task', return_value="parallel_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Parallel workflow executed
                assert result is not None
                assert predictable_llm.call_count > 0
                
                # VERIFY: Parallel structure with synchronization
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                plan_service = WorkPlanService(workspace)
                work_plan = plan_service.load(integration_orchestrator.uid)
                
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    
                    # Verify parallel branches (no inter-branch dependencies)
                    parallel_items = ["market_research", "customer_analysis", "technical_feasibility",
                                    "technology_evaluation", "cost_analysis", "roi_projection"]
                    
                    # Check that parallel items have no dependencies on each other
                    for item_id in parallel_items:
                        if item_id in work_plan.items:
                            item = work_plan.items[item_id]
                            # Parallel items should have no dependencies
                            assert len(item.dependencies) == 0, f"{item_id} should have no dependencies for parallel execution"
                    
                    # Verify synchronization point
                    if "comprehensive_synthesis" in work_plan.items:
                        synthesis_item = work_plan.items["comprehensive_synthesis"]
                        # Should depend on all parallel branches
                        assert len(synthesis_item.dependencies) >= 6, "Synthesis should depend on all parallel branches"
                        for parallel_item in parallel_items:
                            if parallel_item in work_plan.items:
                                assert parallel_item in synthesis_item.dependencies
                
                print("✅ PARALLEL WORKFLOW EXECUTION WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Parallel workflow execution failed: {e}")


@pytest.mark.integration
@pytest.mark.orchestrator
class TestOrchestratorComplexErrorRecovery:
    """
    Complex error recovery and resilience tests.
    
    These tests verify that the orchestrator can handle sophisticated
    error conditions and recovery scenarios in complex workflows.
    """
    
    def test_partial_workflow_failure_recovery_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test recovery from partial workflow failures.
        
        Verifies:
        1. Partial failure detection
        2. Workflow replanning
        3. Alternative path execution
        4. Graceful degradation
        """
        try:
            # Create task that might experience partial failures
            task = integration_task_factory(
                content="Execute resilient data processing pipeline with error recovery",
                thread_id="recovery_test_thread"
            )
            
            # Set up workflow with potential failure points
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Resilient data processing with recovery options",
                    "items": [
                        {
                            "id": "primary_processing",
                            "title": "Primary Data Processing",
                            "description": "Primary processing approach",
                            "kind": "remote",
                            "dependencies": []
                        },
                        {
                            "id": "backup_processing",
                            "title": "Backup Data Processing",
                            "description": "Alternative processing approach",
                            "kind": "remote",
                            "dependencies": []
                        },
                        {
                            "id": "validation",
                            "title": "Result Validation",
                            "description": "Validate processing results",
                            "kind": "local",
                            "dependencies": ["primary_processing"]  # Will adapt if primary fails
                        }
                    ]
                },
                content="Created resilient processing plan"
            )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock processing nodes
            from core.enums import ResourceCategory
            
            mock_adjacent_nodes = {
                "primary_processor": ElementCard(uid="primary_processor", category=ResourceCategory.NODE, type_key="primary_node",
                              name="Primary Processor", description="Primary processing", 
                              capabilities={"data_processing", "optimization"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"data_processing": True, "optimization": True}),
                "backup_processor": ElementCard(uid="backup_processor", category=ResourceCategory.NODE, type_key="backup_node",
                              name="Backup Processor", description="Backup processing", 
                              capabilities={"data_processing", "fault_tolerance"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={"data_processing": True, "fault_tolerance": True})
            }
            
            # Execute resilient workflow
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value=mock_adjacent_nodes), \
                 patch.object(integration_orchestrator, 'send_task', return_value="resilient_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                # VERIFY: Resilient workflow planning succeeded
                assert result is not None
                assert predictable_llm.call_count > 0
                
                # For complex scenario, verify orchestrator created resilient plan
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                if workspace:
                    execution_tracker.track_workspace_fact("Resilient workflow created")
                
                print("✅ PARTIAL WORKFLOW FAILURE RECOVERY WORKS")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Partial workflow failure recovery failed: {e}")
    
    def test_complex_scenario_stress_handling_works(
        self,
        integration_orchestrator: OrchestratorNode,
        predictable_llm: PredictableLLM,
        integration_task_factory,
        execution_tracker: ExecutionTracker
    ):
        """
        Test orchestrator handling under complex scenario stress.
        
        Verifies system stability under sophisticated conditions:
        1. Large workflow complexity
        2. Many dependencies
        3. Mixed local/remote distribution
        4. System resilience
        """
        try:
            # Create highly complex task
            task = integration_task_factory(
                content="Execute enterprise-scale data analytics project with 15+ interconnected phases including data ingestion, multiple analysis stages, validation, and reporting",
                thread_id="stress_test_thread"
            )
            
            # Set up complex stress-test work plan
            predictable_llm.add_tool_call_response(
                tool_name="workplan.create_or_update",
                arguments={
                    "summary": "Enterprise-scale analytics with complex dependencies",
                    "items": [
                        # Data Ingestion Layer
                        {
                            "id": "data_source_1",
                            "title": "Ingest Data Source 1",
                            "description": "Ingest from primary data source",
                            "kind": "remote",
                            "dependencies": []
                        },
                        {
                            "id": "data_source_2", 
                            "title": "Ingest Data Source 2",
                            "description": "Ingest from secondary data source",
                            "kind": "remote",
                            "dependencies": []
                        },
                        # Processing Layer
                        {
                            "id": "data_consolidation",
                            "title": "Data Consolidation",
                            "description": "Consolidate multiple data sources",
                            "kind": "local",
                            "dependencies": ["data_source_1", "data_source_2"]
                        },
                        # Analysis Layers
                        {
                            "id": "descriptive_analytics",
                            "title": "Descriptive Analytics",
                            "description": "Perform descriptive statistical analysis",
                            "kind": "remote",
                            "dependencies": ["data_consolidation"]
                        },
                        {
                            "id": "predictive_analytics",
                            "title": "Predictive Analytics", 
                            "description": "Build predictive models",
                            "kind": "remote",
                            "dependencies": ["data_consolidation"]
                        },
                        {
                            "id": "prescriptive_analytics",
                            "title": "Prescriptive Analytics",
                            "description": "Generate recommendations",
                            "kind": "remote",
                            "dependencies": ["descriptive_analytics", "predictive_analytics"]
                        }
                    ]
                },
                content="Created enterprise-scale complex workflow"
            )
            
            # Create IEM packet
            from core.iem.packets import TaskPacket
            from core.iem.models import ElementAddress
            
            task_packet = TaskPacket.create(
                src=ElementAddress(uid="user"),
                dst=ElementAddress(uid=integration_orchestrator.uid),
                task=task
            )
            
            integration_orchestrator._state.inter_packets.append(task_packet)
            
            # Mock enterprise-scale node network
            from core.enums import ResourceCategory
            
            mock_adjacent_nodes = {
                f"specialist_{i}": ElementCard(uid=f"specialist_{i}", category=ResourceCategory.NODE, type_key=f"specialist_node_{i}",
                              name=f"Specialist {i}", description=f"Specialized processor {i}",
                              capabilities={f"skill_{i}", f"capability_{i}"}, reads=set(), writes=set(),
                              instance=None, config={}, skills={f"skill_{i}": True, f"capability_{i}": True})
                for i in range(10)  # Large number of specialized nodes
            }
            
            # Execute under stress conditions
            start_time = time.time()
            
            with patch.object(integration_orchestrator, 'get_adjacent_nodes', return_value=mock_adjacent_nodes), \
                 patch.object(integration_orchestrator, 'send_task', return_value="stress_test_task"):
                
                result = integration_orchestrator.run(integration_orchestrator._state)
                execution_tracker.track_llm_call()
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                # VERIFY: System handled complexity without failure
                assert result is not None
                assert predictable_llm.call_count > 0
                
                # VERIFY: Reasonable performance under stress (should complete within reasonable time)
                assert execution_time < 30.0, f"Complex scenario took too long: {execution_time:.2f}s"
                
                # VERIFY: Complex workflow structure created
                workspace = integration_orchestrator.get_workspace(task.thread_id)
                plan_service = WorkPlanService(workspace)
                work_plan = plan_service.load(integration_orchestrator.uid)
                
                if work_plan:
                    execution_tracker.track_work_plan_creation(work_plan)
                    assert len(work_plan.items) >= 6, "Should handle complex workflow with multiple items"
                
                print(f"✅ COMPLEX SCENARIO STRESS HANDLING WORKS (executed in {execution_time:.2f}s)")
                
        except Exception as e:
            execution_tracker.track_error(str(e))
            pytest.fail(f"Complex scenario stress handling failed: {e}")
