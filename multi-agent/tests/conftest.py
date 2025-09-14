"""
Global test configuration and shared fixtures.

This module provides common fixtures and configuration for the multi-agent system tests.
Organized by component areas for easy maintenance and reuse.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

# Add the multi-agent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import core types
from elements.llms.common.chat.message import ChatMessage, Role, ToolCall
from elements.tools.common.base_tool import BaseTool
from elements.nodes.common.agent.primitives import AgentAction, AgentObservation, AgentFinish
from elements.nodes.common.agent.parsers import ToolCallParser


# =============================================================================
# AGENT SYSTEM FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_chat():
    """Mock LLM chat function for agent system testing."""
    def _mock_chat(messages: List[ChatMessage], tools: List[BaseTool]) -> ChatMessage:
        # Default response with tool call
        return ChatMessage(
            role=Role.ASSISTANT,
            content="I'll search for information.",
            tool_calls=[
                ToolCall(
                    name="test_tool",
                    args={"query": "test"},
                    tool_call_id="test-call-123"
                )
            ]
        )
    return _mock_chat


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for agent testing."""
    return [
        ChatMessage(role=Role.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=Role.USER, content="What is the weather today?")
    ]


@pytest.fixture
def sample_agent_actions():
    """Sample agent actions for testing."""
    return [
        AgentAction(
            id="action-123",
            tool="test_tool",
            tool_input={"query": "test"},
            reasoning="Need to search for information"
        ),
        AgentAction(
            id="action-456", 
            tool="calculator",
            tool_input={"expression": "2 + 2"},
            reasoning="Need to calculate result"
        )
    ]


@pytest.fixture
def sample_agent_observations():
    """Sample agent observations for testing."""
    return [
        AgentObservation(
            action_id="action-123",
            tool="test_tool",
            output="Tool executed successfully",
            success=True,
            error=None,
            execution_time=0.5
        ),
        AgentObservation(
            action_id="action-456",
            tool="calculator", 
            output="4",
            success=True,
            error=None,
            execution_time=0.1
        )
    ]


@pytest.fixture
def tool_call_parser():
    """Tool call parser instance for testing."""
    return ToolCallParser()


@pytest.fixture
def mock_agent_action_executor():
    """Mock agent action executor for testing."""
    executor = Mock()
    executor.execute.return_value = AgentObservation(
        action_id="action-123",
        tool="test_tool",
        output="Mock tool result",
        success=True,
        error=None,
        execution_time=0.1
    )
    executor.execute_batch.return_value = [
        AgentObservation(
            action_id="action-123",
            tool="test_tool",
            output="Mock tool result",
            success=True,
            error=None,
            execution_time=0.1
        )
    ]
    return executor


# =============================================================================
# TOOL EXECUTION FIXTURES  
# =============================================================================

@pytest.fixture
def mock_tools():
    """Mock tools for testing."""
    tool1 = Mock(spec=BaseTool)
    tool1.name = "test_tool"
    tool1.description = "A test tool"
    
    tool2 = Mock(spec=BaseTool)
    tool2.name = "search_tool"
    tool2.description = "A search tool"
    
    tool3 = Mock(spec=BaseTool)
    tool3.name = "calculator"
    tool3.description = "A calculator tool"
    
    return [tool1, tool2, tool3]


@pytest.fixture
def mock_tool_executor_manager():
    """Mock ToolExecutorManager for testing."""
    manager = Mock()
    manager.has_tool.return_value = True
    manager.execute_requests_async.return_value = Mock()
    manager.get_health.return_value = {"status": "healthy"}
    manager.metrics = {"total_executions": 0, "success_rate": 1.0}
    return manager


# =============================================================================
# LLM INTEGRATION FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    provider = Mock()
    provider.chat.return_value = ChatMessage(
        role=Role.ASSISTANT,
        content="Mock LLM response"
    )
    provider.stream.return_value = iter(["Mock", " streaming", " response"])
    provider.bind_tools.return_value = provider
    return provider


@pytest.fixture
def sample_tool_calls():
    """Sample tool calls for LLM testing."""
    return [
        ToolCall(
            name="search_tool",
            args={"query": "test query", "limit": 5},
            tool_call_id="call-123"
        ),
        ToolCall(
            name="calculator",
            args={"expression": "2 + 2"},
            tool_call_id="call-456"
        )
    ]


# =============================================================================
# STREAMING AND EVENTS FIXTURES
# =============================================================================

@pytest.fixture
def mock_stream_function():
    """Mock streaming function for testing."""
    return Mock()


@pytest.fixture
def captured_stream_events():
    """Capture streaming events for testing."""
    events = []
    
    def capture_event(event):
        events.append(event)
    
    capture_event.events = events
    return capture_event


# =============================================================================
# GRAPH ENGINE FIXTURES (Ready for future implementation)
# =============================================================================

@pytest.fixture
def mock_graph_builder():
    """Mock graph builder for future testing."""
    builder = Mock()
    builder.build.return_value = Mock()
    return builder


@pytest.fixture
def mock_graph_executor():
    """Mock graph executor for future testing."""
    executor = Mock()
    executor.execute.return_value = {"status": "completed"}
    return executor


# =============================================================================
# SESSION MANAGEMENT FIXTURES (Ready for future implementation)
# =============================================================================

@pytest.fixture
def mock_session_manager():
    """Mock session manager for future testing."""
    manager = Mock()
    manager.create_session.return_value = {"session_id": "test-session-123"}
    manager.get_session.return_value = {"session_id": "test-session-123", "state": {}}
    return manager


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def temp_directory(tmp_path):
    """Temporary directory for file-based tests."""
    return tmp_path


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "max_steps": 10,
        "timeout": 30,
        "retry_attempts": 3,
        "debug": True
    }


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "agent_system: Agent system tests")
    config.addinivalue_line("markers", "llm_integration: LLM integration tests")
    config.addinivalue_line("markers", "tool_execution: Tool execution tests")
    config.addinivalue_line("markers", "graph_engine: Graph engine tests")
    config.addinivalue_line("markers", "session_management: Session management tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "fast: Fast running tests")
    config.addinivalue_line("markers", "stable: Stable tests")
    config.addinivalue_line("markers", "flaky: Potentially flaky tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Add markers based on test path
        test_path = str(item.fspath)
        
        if "/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in test_path:
            item.add_marker(pytest.mark.e2e)
            
        if "/agent_system/" in test_path:
            item.add_marker(pytest.mark.agent_system)
        elif "/llm_integration/" in test_path:
            item.add_marker(pytest.mark.llm_integration)
        elif "/tool_execution/" in test_path:
            item.add_marker(pytest.mark.tool_execution)
        elif "/graph_engine/" in test_path:
            item.add_marker(pytest.mark.graph_engine)
        elif "/session_management/" in test_path:
            item.add_marker(pytest.mark.session_management)