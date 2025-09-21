"""
Unit tests for generic tool categorization.

Tests the GenericToolCategorizer and OrchestratorToolCategorizer
for correct tool mapping per PhaseToolMapping configuration.
"""

import pytest
from unittest.mock import Mock
from typing import Set

from elements.nodes.common.agent.phase_tools import (
    GenericToolCategorizer, OrchestratorToolCategorizer,
    create_generic_categorizer, create_orchestrator_categorizer
)
from elements.nodes.common.agent.constants import (
    ExecutionPhase, ToolCategory, ToolKeywords, PhaseToolMapping
)
from elements.tools.common.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, description: str = "Mock tool"):
        self.name = name
        self.description = description
        self.args_schema = None
    
    def _run(self, **kwargs):
        return f"Mock result from {self.name}"


class TestGenericToolCategorizer:
    """Test GenericToolCategorizer."""
    
    def setup_method(self):
        """Set up test tools."""
        self.workplan_tools = [
            MockTool("workplan.create_or_update"),
            MockTool("workplan.assign"),
            MockTool("workplan.mark"),
            MockTool("workplan.summarize")
        ]
        
        self.topology_tools = [
            MockTool("topology.list_adjacent"),
            MockTool("topology.get_node_card")
        ]
        
        self.iem_tools = [
            MockTool("iem.delegate_task"),
            MockTool("delegate_task")
        ]
        
        self.domain_tools = [
            MockTool("calculator"),
            MockTool("file_reader"),
            MockTool("web_search")
        ]
        
        self.all_tools = (
            self.workplan_tools + 
            self.topology_tools + 
            self.iem_tools + 
            self.domain_tools
        )
    
    def test_tool_categorization(self):
        """Test that tools are correctly categorized by prefix."""
        categorizer = GenericToolCategorizer(self.all_tools)
        
        # Check workplan tools
        assert len(categorizer.workplan_tools) == 4
        assert "workplan.create_or_update" in categorizer.workplan_tools
        assert "workplan.assign" in categorizer.workplan_tools
        
        # Check topology tools
        assert len(categorizer.topology_tools) == 2
        assert "topology.list_adjacent" in categorizer.topology_tools
        
        # Check IEM tools
        assert len(categorizer.iem_tools) == 2
        assert "iem.delegate_task" in categorizer.iem_tools
        assert "delegate_task" in categorizer.iem_tools
        
        # Check domain tools
        assert len(categorizer.domain_tools) == 3
        assert "calculator" in categorizer.domain_tools
    
    def test_planning_phase_tools(self):
        """Test tools for planning phase."""
        categorizer = GenericToolCategorizer(self.all_tools)
        planning_tools = categorizer.get_tools_for_phase(ExecutionPhase.PLANNING)
        
        # Should include create/update workplan tools and topology tools
        tool_names = [tool.name for tool in planning_tools]
        
        assert "workplan.create_or_update" in tool_names
        assert "topology.list_adjacent" in tool_names
        assert "topology.get_node_card" in tool_names
        
        # Should not include assign/mark tools
        assert "workplan.assign" not in tool_names
        assert "workplan.mark" not in tool_names
    
    def test_allocation_phase_tools(self):
        """Test tools for allocation phase."""
        categorizer = GenericToolCategorizer(self.all_tools)
        allocation_tools = categorizer.get_tools_for_phase(ExecutionPhase.ALLOCATION)
        
        tool_names = [tool.name for tool in allocation_tools]
        
        # Should include assign/mark workplan tools
        assert "workplan.assign" in tool_names
        assert "workplan.mark" in tool_names
        
        # Should include topology tools for target validation
        assert "topology.list_adjacent" in tool_names
        
        # Should include delegation tools
        assert "iem.delegate_task" in tool_names
        assert "delegate_task" in tool_names
    
    def test_execution_phase_tools(self):
        """Test tools for execution phase."""
        categorizer = GenericToolCategorizer(self.all_tools)
        execution_tools = categorizer.get_tools_for_phase(ExecutionPhase.EXECUTION)
        
        tool_names = [tool.name for tool in execution_tools]
        
        # Should include mark tools for status updates
        assert "workplan.mark" in tool_names
        
        # Should include domain tools for local execution
        assert "calculator" in tool_names
        assert "file_reader" in tool_names
        assert "web_search" in tool_names
    
    def test_monitoring_phase_tools(self):
        """Test tools for monitoring phase."""
        categorizer = GenericToolCategorizer(self.all_tools)
        monitoring_tools = categorizer.get_tools_for_phase(ExecutionPhase.MONITORING)
        
        tool_names = [tool.name for tool in monitoring_tools]
        
        # Should include workplan management tools
        assert "workplan.mark" in tool_names
        # Note: ingest and complete tools would be here if they existed in our mock set
    
    def test_synthesis_phase_tools(self):
        """Test tools for synthesis phase."""
        categorizer = GenericToolCategorizer(self.all_tools)
        synthesis_tools = categorizer.get_tools_for_phase(ExecutionPhase.SYNTHESIS)
        
        tool_names = [tool.name for tool in synthesis_tools]
        
        # Should include summarize tools
        assert "workplan.summarize" in tool_names
    
    def test_get_all_phase_tools(self):
        """Test getting all phase-to-tools mappings."""
        categorizer = GenericToolCategorizer(self.all_tools)
        all_phase_tools = categorizer.get_all_phase_tools()
        
        # Should have all phases
        assert ExecutionPhase.PLANNING in all_phase_tools
        assert ExecutionPhase.ALLOCATION in all_phase_tools
        assert ExecutionPhase.EXECUTION in all_phase_tools
        assert ExecutionPhase.MONITORING in all_phase_tools
        assert ExecutionPhase.SYNTHESIS in all_phase_tools
        
        # Each phase should have tools
        for phase, tools in all_phase_tools.items():
            assert isinstance(tools, list)
            assert len(tools) > 0
    
    def test_add_custom_phase(self):
        """Test adding a custom phase."""
        categorizer = GenericToolCategorizer(self.all_tools)
        
        # Add custom phase that only includes domain tools
        categorizer.add_custom_phase(
            ExecutionPhase.EXECUTION,  # Reuse existing enum for test
            keywords=set(),
            categories={ToolCategory.DOMAIN}
        )
        
        # Should override the default execution phase tools
        execution_tools = categorizer.get_tools_for_phase(ExecutionPhase.EXECUTION)
        tool_names = [tool.name for tool in execution_tools]
        
        assert "calculator" in tool_names
        assert "file_reader" in tool_names
        assert "web_search" in tool_names
    
    def test_get_tool_categories(self):
        """Test getting tools organized by category."""
        categorizer = GenericToolCategorizer(self.all_tools)
        categories = categorizer.get_tool_categories()
        
        assert "workplan" in categories
        assert "topology" in categories
        assert "iem" in categories
        assert "domain" in categories
        
        assert len(categories["workplan"]) == 4
        assert len(categories["topology"]) == 2
        assert len(categories["iem"]) == 2
        assert len(categories["domain"]) == 3
    
    def test_custom_phase_mappings(self):
        """Test custom phase mappings in constructor."""
        custom_mappings = {
            ExecutionPhase.PLANNING: {
                "keywords": {"create"},
                "categories": {ToolCategory.WORKPLAN}
            }
        }
        
        categorizer = GenericToolCategorizer(
            self.all_tools,
            custom_phase_mappings=custom_mappings
        )
        
        planning_tools = categorizer.get_tools_for_phase(ExecutionPhase.PLANNING)
        tool_names = [tool.name for tool in planning_tools]
        
        # Should only include create tools
        assert "workplan.create_or_update" in tool_names
        # Should not include topology tools (not in custom mapping)
        assert "topology.list_adjacent" not in tool_names


class TestOrchestratorToolCategorizer:
    """Test OrchestratorToolCategorizer."""
    
    def setup_method(self):
        """Set up test tools."""
        self.tools = [
            MockTool("workplan.create_or_update"),
            MockTool("topology.list_adjacent"),
            MockTool("iem.delegate_task"),
            MockTool("delegate_task"),
            MockTool("calculator")
        ]
    
    def test_orchestrator_specific_categorization(self):
        """Test orchestrator-specific tool categorization."""
        categorizer = OrchestratorToolCategorizer(self.tools)
        
        # Should inherit from generic categorizer
        assert hasattr(categorizer, 'workplan_tools')
        assert hasattr(categorizer, 'iem_tools')
        
        # Should have orchestrator-specific methods
        delegation_tools = categorizer.get_delegation_tools()
        tool_names = [tool.name for tool in delegation_tools]
        
        assert "iem.delegate_task" in tool_names
        assert "delegate_task" in tool_names
    
    def test_orchestrator_planning_tools(self):
        """Test orchestrator planning tools."""
        categorizer = OrchestratorToolCategorizer(self.tools)
        planning_tools = categorizer.get_planning_tools()
        
        # Should be same as generic planning tools
        tool_names = [tool.name for tool in planning_tools]
        assert "workplan.create_or_update" in tool_names
        assert "topology.list_adjacent" in tool_names
    
    def test_orchestrator_allocation_tools(self):
        """Test orchestrator allocation tools."""
        categorizer = OrchestratorToolCategorizer(self.tools)
        allocation_tools = categorizer.get_allocation_tools()
        
        tool_names = [tool.name for tool in allocation_tools]
        
        # Should include delegation tools
        assert "iem.delegate_task" in tool_names
        assert "delegate_task" in tool_names


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_create_generic_categorizer(self):
        """Test generic categorizer factory."""
        tools = [MockTool("test_tool")]
        categorizer = create_generic_categorizer(tools)
        
        assert isinstance(categorizer, GenericToolCategorizer)
        assert len(categorizer.all_tools) == 1
    
    def test_create_orchestrator_categorizer(self):
        """Test orchestrator categorizer factory."""
        tools = [MockTool("test_tool")]
        categorizer = create_orchestrator_categorizer(tools)
        
        assert isinstance(categorizer, OrchestratorToolCategorizer)
        assert len(categorizer.all_tools) == 1
        
        # Should have orchestrator-specific methods
        assert hasattr(categorizer, 'get_delegation_tools')
        assert hasattr(categorizer, 'get_planning_tools')
        assert hasattr(categorizer, 'get_allocation_tools')


