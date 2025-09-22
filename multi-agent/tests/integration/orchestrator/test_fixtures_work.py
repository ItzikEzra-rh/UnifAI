"""
Simple test to verify our SOLID fixtures work correctly.
"""

import pytest


@pytest.mark.integration
class TestFixturesWork:
    """Verify that our SOLID integration fixtures work correctly."""
    
    def test_predictable_llm_fixture_works(self, predictable_llm):
        """Test that the predictable LLM fixture works."""
        # Add a response
        predictable_llm.add_response("Test response from fixture")
        
        # Call the LLM
        from elements.llms.common.chat.message import ChatMessage, Role
        messages = [ChatMessage(role=Role.USER, content="Test")]
        
        response = predictable_llm.chat(messages)
        
        # Verify it works
        assert response.content == "Test response from fixture"
        assert predictable_llm.call_count == 1
        
        print("✅ PredictableLLM fixture works!")
    
    def test_execution_tracker_fixture_works(self, execution_tracker):
        """Test that the execution tracker fixture works."""
        # Track some execution
        execution_tracker.track_llm_call()
        execution_tracker.track_workspace_fact("Test fact")
        
        # Verify it works
        assert execution_tracker.verify_basic_execution()
        summary = execution_tracker.get_summary()
        assert summary["success"] == True
        
        print("✅ ExecutionTracker fixture works!")
    
    def test_orchestrator_integration_state_fixture_works(self, orchestrator_integration_state):
        """Test that the integration state fixture works."""
        # Verify state is set up
        assert orchestrator_integration_state is not None
        
        # StateView should have access to channels we need
        assert hasattr(orchestrator_integration_state, 'workspaces')
        assert hasattr(orchestrator_integration_state, 'task_threads')
        assert hasattr(orchestrator_integration_state, 'threads')
        
        # Test that we can access the workspace data
        workspaces = orchestrator_integration_state.workspaces
        assert workspaces is not None
        assert isinstance(workspaces, dict)
        
        print("✅ OrchestratorIntegrationState fixture works!")
    
    def test_workspace_service_fixture_works(self, orchestrator_workspace_service):
        """Test that the workspace service fixture works."""
        # Verify service is available
        assert orchestrator_workspace_service is not None
        
        # Test basic operations
        thread_id = "test_thread_fixture"
        workspace = orchestrator_workspace_service.get_workspace(thread_id)
        assert workspace is not None
        assert workspace.thread_id == thread_id
        
        print("✅ OrchestratorWorkspaceService fixture works!")
    
    def test_integration_orchestrator_fixture_works(self, integration_orchestrator, predictable_llm):
        """Test that the integration orchestrator fixture works."""
        # Verify orchestrator is set up
        assert integration_orchestrator is not None
        assert integration_orchestrator.uid == "test_orchestrator"
        
        # Verify it has the predictable LLM
        assert integration_orchestrator.llm == predictable_llm
        
        # Verify it can access workspace
        workspace = integration_orchestrator.get_workspace("test_thread")
        assert workspace is not None
        
        print("✅ IntegrationOrchestrator fixture works!")
    
    def test_task_factory_fixture_works(self, integration_task_factory):
        """Test that the task factory fixture works."""
        # Create a task
        task = integration_task_factory("Test task content", "test_thread")
        
        # Verify task is created correctly
        assert task.content == "Test task content"
        assert task.thread_id == "test_thread"
        assert task.created_by == "integration_test"
        
        print("✅ IntegrationTaskFactory fixture works!")
    
    def test_all_fixtures_work_together(
        self,
        integration_orchestrator,
        predictable_llm,
        orchestrator_workspace_service,
        integration_task_factory,
        execution_tracker
    ):
        """Test that all fixtures work together properly."""
        # Set up LLM response
        predictable_llm.add_response("All fixtures working together!")
        
        # Create a task
        task = integration_task_factory("Integration test task")
        
        # Track execution
        execution_tracker.track_llm_call()
        execution_tracker.track_workspace_fact("Integration test started")
        
        # Add fact to workspace via orchestrator
        integration_orchestrator.add_fact_to_workspace(task.thread_id, "Test fact via orchestrator")
        
        # Get workspace via service
        workspace = orchestrator_workspace_service.get_workspace(task.thread_id)
        
        # Verify everything works
        assert workspace is not None
        assert "Test fact via orchestrator" in workspace.context.facts
        assert execution_tracker.verify_basic_execution()
        
        print("🎉 ALL FIXTURES WORK TOGETHER PERFECTLY!")
