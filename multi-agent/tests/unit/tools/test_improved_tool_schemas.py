"""
Unit tests for improved tool schemas.

Tests the enhanced Pydantic schemas for orchestration tools,
including validation, error handling, and LLM guidance.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pydantic import ValidationError

from elements.tools.builtin.workplan.create_or_update import (
    CreateOrUpdateWorkPlanTool, CreateOrUpdatePlanArgs, WorkItemSpec
)
from elements.tools.builtin.delegation.delegate_task import (
    DelegateTaskTool, DelegateTaskArgs
)
from elements.tools.builtin.workplan.summarize import SummarizeWorkPlanTool
from elements.nodes.common.workload import WorkItemKind


class TestWorkItemSpec:
    """Test WorkItemSpec Pydantic model."""
    
    def test_minimal_work_item_spec(self):
        """Test creating work item spec with minimal fields."""
        spec = WorkItemSpec(
            id="analyze_data",
            title="Analyze Sales Data",
            description="Extract and analyze Q4 sales metrics from database"
        )
        
        assert spec.id == "analyze_data"
        assert spec.title == "Analyze Sales Data"
        assert spec.description == "Extract and analyze Q4 sales metrics from database"
        assert spec.dependencies == []
        assert spec.kind == WorkItemKind.REMOTE  # Default
        assert spec.estimated_duration is None
    
    def test_full_work_item_spec(self):
        """Test creating work item spec with all fields."""
        spec = WorkItemSpec(
            id="create_presentation",
            title="Create Q4 Presentation",
            description="Create PowerPoint presentation with Q4 analysis and charts",
            dependencies=["analyze_data", "generate_charts"],
            kind=WorkItemKind.LOCAL,
            estimated_duration="2 hours"
        )
        
        assert spec.id == "create_presentation"
        assert spec.title == "Create Q4 Presentation"
        assert spec.dependencies == ["analyze_data", "generate_charts"]
        assert spec.kind == WorkItemKind.LOCAL
        assert spec.estimated_duration == "2 hours"
    
    def test_work_item_spec_validation(self):
        """Test WorkItemSpec validation."""
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            WorkItemSpec()
        errors = exc_info.value.errors()
        required_fields = {error['loc'][0] for error in errors if error['type'] == 'missing'}
        assert 'id' in required_fields
        assert 'title' in required_fields
        assert 'description' in required_fields
        
        # Invalid enum value
        with pytest.raises(ValidationError):
            WorkItemSpec(
                id="test", title="Test", description="Test",
                kind="invalid_kind"
            )
    
    def test_work_item_spec_id_guidance(self):
        """Test that ID field has helpful guidance."""
        # The description should guide users to use snake_case
        field_info = WorkItemSpec.model_fields['id']
        assert 'snake_case' in field_info.description
        assert 'analyze_data' in field_info.description


class TestCreateOrUpdatePlanArgs:
    """Test CreateOrUpdatePlanArgs Pydantic model."""
    
    def test_valid_plan_args(self):
        """Test valid plan arguments."""
        items = [
            WorkItemSpec(
                id="task1",
                title="First Task", 
                description="Do the first thing"
            ),
            WorkItemSpec(
                id="task2",
                title="Second Task",
                description="Do the second thing",
                dependencies=["task1"]
            )
        ]
        
        args = CreateOrUpdatePlanArgs(
            summary="Complete project workflow",
            items=items
        )
        
        assert args.summary == "Complete project workflow"
        assert len(args.items) == 2
        assert args.items[0].id == "task1"
        assert args.items[1].dependencies == ["task1"]
    
    def test_plan_args_validation(self):
        """Test plan arguments validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            CreateOrUpdatePlanArgs()
        
        # Empty items list should fail (min_items=1)
        with pytest.raises(ValidationError):
            CreateOrUpdatePlanArgs(
                summary="Test",
                items=[]
            )
    
    def test_plan_args_descriptions(self):
        """Test that field descriptions are helpful."""
        summary_field = CreateOrUpdatePlanArgs.model_fields['summary']
        items_field = CreateOrUpdatePlanArgs.model_fields['items']
        
        # Summary should have example
        assert 'Analyze Q4 sales data and create presentation' in summary_field.description
        
        # Items should mention dependencies
        assert 'dependencies' in items_field.description.lower()


class TestCreateOrUpdateWorkPlanTool:
    """Test CreateOrUpdateWorkPlanTool with improved schema."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_workspace = Mock()
        self.mock_service = Mock()
        self.mock_plan = Mock()
        
        # Mock accessors
        self.get_workspace = Mock(return_value=self.mock_workspace)
        self.get_thread_id = Mock(return_value="thread-123")
        self.get_owner_uid = Mock(return_value="orchestrator-1")
        
        self.tool = CreateOrUpdateWorkPlanTool(
            get_workspace=self.get_workspace,
            get_thread_id=self.get_thread_id,
            get_owner_uid=self.get_owner_uid
        )
    
    def test_tool_description_guidance(self):
        """Test that tool description provides clear guidance."""
        description = self.tool.description
        
        # Should mention breaking down tasks
        assert 'break down' in description.lower()
        # Should mention dependencies
        assert 'dependencies' in description.lower()
        # Should mention LOCAL vs REMOTE
        assert 'LOCAL' in description and 'REMOTE' in description
        # Should mention delegation
        assert 'delegation' in description.lower()
    
    def test_tool_schema_validation(self):
        """Test that tool validates arguments properly."""
        # Valid arguments should work
        valid_args = {
            "summary": "Test project",
            "items": [
                {
                    "id": "task1",
                    "title": "First Task",
                    "description": "Do something"
                }
            ]
        }
        
        # Should not raise validation error
        parsed_args = CreateOrUpdatePlanArgs(**valid_args)
        assert parsed_args.summary == "Test project"
        
        # Invalid arguments should fail
        invalid_args = {
            "summary": "Test project",
            "items": []  # Empty list violates min_items=1
        }
        
        with pytest.raises(ValidationError):
            CreateOrUpdatePlanArgs(**invalid_args)
    
    @pytest.fixture
    def mock_workplan_service(self):
        """Mock WorkPlanService for testing."""
        with pytest.patch('elements.tools.builtin.workplan.create_or_update.WorkPlanService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock plan creation/loading
            mock_plan = Mock()
            mock_plan.items = {}
            mock_service.load.return_value = None  # No existing plan
            mock_service.create.return_value = mock_plan
            mock_service.save.return_value = True
            
            yield mock_service
    
    def test_tool_execution_with_structured_items(self, mock_workplan_service):
        """Test tool execution with structured work items."""
        # Test data with dependencies
        args = {
            "summary": "Q4 Analysis Project",
            "items": [
                {
                    "id": "extract_data",
                    "title": "Extract Q4 Data",
                    "description": "Extract sales data from database",
                    "kind": "remote"
                },
                {
                    "id": "analyze_data", 
                    "title": "Analyze Data",
                    "description": "Perform statistical analysis",
                    "dependencies": ["extract_data"],
                    "kind": "remote"
                },
                {
                    "id": "create_report",
                    "title": "Create Report",
                    "description": "Generate final report",
                    "dependencies": ["analyze_data"],
                    "kind": "local",
                    "estimated_duration": "1 hour"
                }
            ]
        }
        
        result = self.tool.run(**args)
        
        # Should succeed
        assert result["success"] is True
        assert result["total_items"] == 3
        
        # Verify service interactions
        mock_workplan_service.create.assert_called_once()
        mock_workplan_service.save.assert_called_once()
        
        # Verify plan was updated with correct summary
        create_call = mock_workplan_service.create.call_args
        # The plan should be created and then updated
        
        # Verify items were added with correct structure
        # (This would require mocking the WorkItem creation)


class TestDelegateTaskArgs:
    """Test DelegateTaskArgs improved schema."""
    
    def test_valid_delegate_args(self):
        """Test valid delegation arguments."""
        args = DelegateTaskArgs(
            dst_uid="data_analyst_node",
            content="Analyze Q4 sales data and provide summary with key metrics",
            thread_id="thread-123",
            parent_item_id="analyze_q4_data",
            should_respond=True,
            data={"query_type": "sales", "period": "Q4"}
        )
        
        assert args.dst_uid == "data_analyst_node"
        assert args.content == "Analyze Q4 sales data and provide summary with key metrics"
        assert args.thread_id == "thread-123"
        assert args.parent_item_id == "analyze_q4_data"
        assert args.should_respond is True
        assert args.data == {"query_type": "sales", "period": "Q4"}
    
    def test_delegate_args_validation(self):
        """Test delegation arguments validation."""
        # Missing required fields
        with pytest.raises(ValidationError):
            DelegateTaskArgs()
        
        # Valid minimal args
        args = DelegateTaskArgs(
            dst_uid="worker_node",
            content="Do some work",
            thread_id="thread-123"
        )
        
        assert args.parent_item_id is None  # Optional
        assert args.should_respond is True  # Default
        assert args.data == {}  # Default
    
    def test_delegate_args_descriptions(self):
        """Test that field descriptions provide guidance."""
        dst_uid_field = DelegateTaskArgs.model_fields['dst_uid']
        content_field = DelegateTaskArgs.model_fields['content']
        parent_item_id_field = DelegateTaskArgs.model_fields['parent_item_id']
        
        # dst_uid should mention checking adjacency
        assert 'ListAdjacentNodesTool' in dst_uid_field.description
        
        # content should mention being detailed
        assert 'detailed' in content_field.description.lower()
        assert 'deliverables' in content_field.description.lower()
        
        # parent_item_id should mention tracking
        assert 'track' in parent_item_id_field.description.lower()


class TestDelegateTaskTool:
    """Test DelegateTaskTool with improved schema."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_send_task = Mock(return_value="packet-123")
        self.mock_get_owner_uid = Mock(return_value="orchestrator-1")
        self.mock_get_workspace = Mock()
        self.mock_check_adjacency = Mock(return_value=True)
        
        self.tool = DelegateTaskTool(
            send_task=self.mock_send_task,
            get_owner_uid=self.mock_get_owner_uid,
            get_workspace=self.mock_get_workspace,
            check_adjacency=self.mock_check_adjacency
        )
    
    def test_tool_description_guidance(self):
        """Test that tool description provides clear guidance."""
        description = self.tool.description
        
        # Should mention when to use
        assert 'capabilities' in description.lower()
        # Should mention parent_item_id importance
        assert 'parent_item_id' in description
        # Should mention automatic responses
        assert 'automatically' in description.lower()
    
    def test_adjacency_validation_error_message(self):
        """Test that adjacency errors have helpful messages."""
        # Mock adjacency check to fail
        self.mock_check_adjacency.return_value = False
        
        result = self.tool.run(
            dst_uid="unknown_node",
            content="Do something",
            thread_id="thread-123"
        )
        
        assert result["success"] is False
        error_msg = result["error"]
        # Should have helpful error message (updated by user)
        assert "not adjacent" in error_msg
        assert "check what it is really adjacent" in error_msg


class TestSummarizeWorkPlanTool:
    """Test SummarizeWorkPlanTool with improved functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_workspace = Mock()
        self.mock_get_workspace = Mock(return_value=self.mock_workspace)
        self.mock_get_owner_uid = Mock(return_value="orchestrator-1")
        
        self.tool = SummarizeWorkPlanTool(
            get_workspace=self.mock_get_workspace,
            get_owner_uid=self.mock_get_owner_uid
        )
    
    def test_tool_description_synthesis_focus(self):
        """Test that tool description focuses on synthesis phase."""
        description = self.tool.description
        
        # Should mention SYNTHESIS phase
        assert 'SYNTHESIS' in description
        # Should mention final report
        assert 'final report' in description.lower()
        # Should mention results and deliverables
        assert 'results' in description.lower()
        assert 'deliverables' in description.lower()
    
    @pytest.fixture
    def mock_workplan_service_with_results(self):
        """Mock WorkPlanService with completed work items."""
        with pytest.patch('elements.tools.builtin.workplan.summarize.WorkPlanService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock plan with completed items
            mock_plan = Mock()
            mock_plan.summary = "Q4 Analysis Project"
            mock_plan.get_status_counts.return_value = Mock(
                pending=0, in_progress=0, waiting=0, done=2, failed=0, blocked=0
            )
            
            # Mock completed items with results
            completed_item1 = Mock()
            completed_item1.title = "Extract Q4 Data"
            completed_item1.result_ref = Mock()
            completed_item1.result_ref.content = "Successfully extracted 10,000 sales records"
            completed_item1.assigned_uid = "data_extractor_node"
            
            completed_item2 = Mock()
            completed_item2.title = "Analyze Data"
            completed_item2.result_ref = Mock()
            completed_item2.result_ref.content = "Analysis complete: 15% growth, top product Widget Pro"
            completed_item2.assigned_uid = "data_analyst_node"
            
            mock_plan.get_items_by_status.return_value = [completed_item1, completed_item2]
            mock_service.load.return_value = mock_plan
            
            yield mock_service
    
    def test_enhanced_summary_with_results(self, mock_workplan_service_with_results):
        """Test that summary includes results and completion details."""
        result = self.tool.run()
        
        summary = result["summary"]
        
        # Should include project summary
        assert "Q4 Analysis Project" in summary
        
        # Should include completed work with results
        assert "Completed Work" in summary
        assert "Extract Q4 Data" in summary
        assert "Successfully extracted 10,000 sales records" in summary
        assert "data_extractor_node" in summary
        
        # Should include analysis results
        assert "Analyze Data" in summary
        assert "15% growth" in summary
        assert "data_analyst_node" in summary
        
        # Should use checkmarks for completed items
        assert "✅" in summary


class TestToolSchemaConsistency:
    """Test consistency across all improved tool schemas."""
    
    def test_all_tools_have_helpful_descriptions(self):
        """Test that all tools have helpful descriptions."""
        tools = [
            CreateOrUpdateWorkPlanTool,
            DelegateTaskTool,
            SummarizeWorkPlanTool
        ]
        
        for tool_class in tools:
            # Create mock instance to access description
            if tool_class == CreateOrUpdateWorkPlanTool:
                tool = tool_class(Mock(), Mock(), Mock())
            elif tool_class == DelegateTaskTool:
                tool = tool_class(Mock(), Mock(), Mock())
            else:  # SummarizeWorkPlanTool
                tool = tool_class(Mock(), Mock())
            
            description = tool.description
            
            # Should be substantial (not just one line)
            assert len(description) > 50
            # Should contain guidance words
            guidance_words = ['use', 'when', 'should', 'include', 'provide']
            assert any(word in description.lower() for word in guidance_words)
    
    def test_pydantic_models_have_field_descriptions(self):
        """Test that Pydantic models have helpful field descriptions."""
        models = [
            WorkItemSpec,
            CreateOrUpdatePlanArgs,
            DelegateTaskArgs
        ]
        
        for model_class in models:
            fields = model_class.model_fields
            
            # All fields should have descriptions
            for field_name, field_info in fields.items():
                assert field_info.description is not None
                assert len(field_info.description) > 10  # Substantial description
    
    def test_validation_error_quality(self):
        """Test that validation errors are informative."""
        # Test WorkItemSpec validation
        try:
            WorkItemSpec(id="test")  # Missing title and description
        except ValidationError as e:
            errors = e.errors()
            # Should have clear error messages
            assert len(errors) >= 2  # Missing title and description
            for error in errors:
                assert 'required' in error['type'] or 'missing' in error['type']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

