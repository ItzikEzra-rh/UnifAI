"""
Unit tests for orchestrator system message separation.

Tests the separation of domain specialization from orchestrator behavior
to ensure clean separation of concerns.
"""

import pytest
from unittest.mock import Mock, patch

from elements.nodes.orchestrator.orchestrator_node import OrchestratorNode
from elements.tools.common.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.description = f"Mock {name} tool"
        self.args_schema = None
    
    def run(self, **kwargs):
        return {"success": True, "result": f"Mock result from {self.name}"}


class TestOrchestratorSystemMessageSeparation:
    """Test system message separation functionality."""
    
    def test_orchestrator_behavior_message_content(self):
        """Test that orchestrator behavior message contains expected content."""
        behavior_msg = OrchestratorNode._get_orchestrator_behavior_message()
        
        # Should contain core orchestrator responsibilities
        assert "orchestrator agent" in behavior_msg.lower()
        assert "coordinate work execution" in behavior_msg.lower()
        
        # Should mention key responsibilities
        assert "work plans" in behavior_msg.lower()
        assert "delegate" in behavior_msg.lower()
        assert "monitor" in behavior_msg.lower()
        assert "synthesize" in behavior_msg.lower()
        
        # Should contain guidelines
        assert "guidelines" in behavior_msg.lower()
        assert "dependencies" in behavior_msg.lower()
        assert "capabilities" in behavior_msg.lower()
        assert "correlation" in behavior_msg.lower()
    
    def test_orchestrator_behavior_message_consistency(self):
        """Test that orchestrator behavior message is consistent across calls."""
        msg1 = OrchestratorNode._get_orchestrator_behavior_message()
        msg2 = OrchestratorNode._get_orchestrator_behavior_message()
        
        # Should be identical (static method)
        assert msg1 == msg2
        
        # Should be substantial
        assert len(msg1) > 200, "Behavior message should be comprehensive"
    
    def test_build_complete_system_message_no_specialization(self):
        """Test building complete system message without domain specialization."""
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=""  # No domain specialization
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should contain only orchestrator behavior
        assert "orchestrator agent" in complete_msg.lower()
        assert "coordinate work execution" in complete_msg.lower()
        
        # Should not contain domain specialization section
        assert "Domain Specialization:" not in complete_msg
    
    def test_build_complete_system_message_with_specialization(self):
        """Test building complete system message with domain specialization."""
        domain_specialization = "I specialize in document analysis and Slack integration"
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=domain_specialization
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should contain orchestrator behavior
        assert "orchestrator agent" in complete_msg.lower()
        assert "coordinate work execution" in complete_msg.lower()
        
        # Should contain domain specialization section
        assert "Domain Specialization:" in complete_msg
        assert domain_specialization in complete_msg
        
        # Should have proper structure
        behavior_part = complete_msg.split("Domain Specialization:")[0]
        specialization_part = complete_msg.split("Domain Specialization:")[1]
        
        assert "orchestrator agent" in behavior_part.lower()
        assert domain_specialization in specialization_part
    
    def test_domain_specialization_storage(self):
        """Test that domain specialization is stored separately."""
        domain_specialization = "I specialize in financial data analysis and reporting"
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=domain_specialization
        )
        
        # Should store domain specialization separately
        assert orchestrator.domain_specialization == domain_specialization
        
        # System message should be the complete message
        complete_msg = orchestrator.system_message
        assert domain_specialization in complete_msg
        assert "orchestrator agent" in complete_msg.lower()
    
    def test_system_message_used_in_strategy_creation(self):
        """Test that complete system message is used in strategy creation."""
        domain_specialization = "I specialize in customer service automation"
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=domain_specialization
        )
        
        # Mock dependencies
        orchestrator.get_workspace = Mock(return_value=Mock())
        orchestrator.get_adjacent_nodes = Mock(return_value=["worker_node"])
        
        with patch.object(orchestrator, 'create_strategy') as mock_create_strategy:
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy
            
            # Trigger strategy creation
            orchestrator._run_orchestration_cycle("test_thread", "test content")
            
            # Verify strategy was created with complete system message
            mock_create_strategy.assert_called_once()
            call_args = mock_create_strategy.call_args
            
            # Should use complete system message (behavior + specialization)
            system_message_arg = call_args[1]['system_message']
            assert "orchestrator agent" in system_message_arg.lower()
            assert domain_specialization in system_message_arg
            assert "Domain Specialization:" in system_message_arg


class TestOrchestratorSystemMessageVariations:
    """Test various system message scenarios."""
    
    def test_empty_string_specialization(self):
        """Test with empty string specialization."""
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=""
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should contain only behavior message
        assert "orchestrator agent" in complete_msg.lower()
        assert "Domain Specialization:" not in complete_msg
        assert orchestrator.domain_specialization == ""
    
    def test_none_specialization(self):
        """Test with None specialization."""
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")]
            # system_message defaults to ""
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should contain only behavior message
        assert "orchestrator agent" in complete_msg.lower()
        assert "Domain Specialization:" not in complete_msg
        assert orchestrator.domain_specialization == ""
    
    def test_whitespace_only_specialization(self):
        """Test with whitespace-only specialization."""
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message="   \n\t   "
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should still include specialization section (even if whitespace)
        assert "Domain Specialization:" in complete_msg
        assert "   \n\t   " in complete_msg
    
    def test_long_specialization_message(self):
        """Test with long domain specialization message."""
        long_specialization = """
        I am a highly specialized orchestrator focused on complex financial data processing workflows.
        My expertise includes:
        - Real-time market data analysis and processing
        - Risk assessment and compliance checking
        - Automated report generation for regulatory bodies
        - Integration with multiple financial data providers
        - High-frequency trading data reconciliation
        - Portfolio optimization and rebalancing
        
        I work with adjacent nodes including:
        - Market data ingestion services
        - Risk calculation engines  
        - Compliance validation systems
        - Report generation services
        - Notification and alerting systems
        
        I prioritize accuracy, compliance, and real-time processing capabilities.
        """
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=long_specialization
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should contain both behavior and full specialization
        assert "orchestrator agent" in complete_msg.lower()
        assert "Domain Specialization:" in complete_msg
        assert "financial data processing" in complete_msg
        assert "risk assessment" in complete_msg
        assert "compliance" in complete_msg
        
        # Should maintain structure
        parts = complete_msg.split("Domain Specialization:")
        assert len(parts) == 2
        assert "orchestrator agent" in parts[0].lower()
        assert "financial data processing" in parts[1]
    
    def test_specialization_with_special_characters(self):
        """Test specialization with special characters."""
        special_specialization = """
        I specialize in:
        • Document processing & analysis
        • Multi-language support (English, 中文, Español)
        • API integration → REST/GraphQL
        • Data formats: JSON, XML, CSV, Parquet
        • Regex patterns: /^[A-Z]{2,3}-\\d{4}$/
        """
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("test_tool")],
            system_message=special_specialization
        )
        
        complete_msg = orchestrator._build_complete_system_message()
        
        # Should preserve special characters
        assert "•" in complete_msg
        assert "中文" in complete_msg
        assert "→" in complete_msg
        assert "/^[A-Z]{2,3}-\\d{4}$/" in complete_msg
        
        # Should still have proper structure
        assert "Domain Specialization:" in complete_msg
        assert "orchestrator agent" in complete_msg.lower()


class TestOrchestratorSystemMessageIntegration:
    """Test system message integration with other components."""
    
    def test_system_message_in_agent_execution(self):
        """Test that system message is properly used in agent execution."""
        domain_specialization = "I specialize in e-commerce order processing"
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("order_tool")],
            system_message=domain_specialization
        )
        
        # Mock dependencies
        orchestrator.get_workspace = Mock(return_value=Mock())
        orchestrator.get_adjacent_nodes = Mock(return_value=["order_processor"])
        
        with patch.object(orchestrator, 'create_strategy') as mock_create_strategy:
            with patch.object(orchestrator, 'execute_agent') as mock_execute:
                mock_strategy = Mock()
                mock_create_strategy.return_value = mock_strategy
                mock_execute.return_value = Mock(is_complete=True)
                
                # Run orchestration cycle
                orchestrator._run_orchestration_cycle("test_thread", "process order")
                
                # Verify strategy creation used complete message
                mock_create_strategy.assert_called_once()
                strategy_args = mock_create_strategy.call_args[1]
                
                system_message = strategy_args['system_message']
                assert "orchestrator agent" in system_message.lower()
                assert domain_specialization in system_message
                assert "e-commerce order processing" in system_message
    
    def test_system_message_consistency_across_cycles(self):
        """Test that system message is consistent across multiple orchestration cycles."""
        domain_specialization = "I specialize in data pipeline orchestration"
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("pipeline_tool")],
            system_message=domain_specialization
        )
        
        # Mock dependencies
        orchestrator.get_workspace = Mock(return_value=Mock())
        orchestrator.get_adjacent_nodes = Mock(return_value=["data_processor"])
        
        system_messages_used = []
        
        def capture_system_message(*args, **kwargs):
            system_messages_used.append(kwargs.get('system_message'))
            return Mock()
        
        with patch.object(orchestrator, 'create_strategy', side_effect=capture_system_message):
            with patch.object(orchestrator, 'execute_agent') as mock_execute:
                mock_execute.return_value = Mock(is_complete=True)
                
                # Run multiple orchestration cycles
                orchestrator._run_orchestration_cycle("thread1", "task1")
                orchestrator._run_orchestration_cycle("thread2", "task2")
                orchestrator._run_orchestration_cycle("thread3", "task3")
                
                # Verify all system messages are identical
                assert len(system_messages_used) == 3
                assert system_messages_used[0] == system_messages_used[1]
                assert system_messages_used[1] == system_messages_used[2]
                
                # Verify content
                for msg in system_messages_used:
                    assert "orchestrator agent" in msg.lower()
                    assert domain_specialization in msg
    
    def test_domain_specialization_accessibility(self):
        """Test that domain specialization is accessible for adjacency info."""
        domain_specialization = "I specialize in machine learning model training and deployment"
        
        orchestrator = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("ml_tool")],
            system_message=domain_specialization
        )
        
        # Domain specialization should be accessible separately
        assert orchestrator.domain_specialization == domain_specialization
        
        # This could be used by other orchestrators to understand capabilities
        assert "machine learning" in orchestrator.domain_specialization
        assert "model training" in orchestrator.domain_specialization
        assert "deployment" in orchestrator.domain_specialization
    
    def test_behavior_message_independence(self):
        """Test that behavior message is independent of domain specialization."""
        # Create two orchestrators with different specializations
        orchestrator1 = OrchestratorNode(
            llm=Mock(),
            tools=[MockTool("tool1")],
            system_message="I specialize in web scraping"
        )
        
        orchestrator2 = OrchestratorNode(
            llm=Mock(), 
            tools=[MockTool("tool2")],
            system_message="I specialize in image processing"
        )
        
        # Behavior messages should be identical
        behavior1 = OrchestratorNode._get_orchestrator_behavior_message()
        behavior2 = OrchestratorNode._get_orchestrator_behavior_message()
        assert behavior1 == behavior2
        
        # Complete messages should differ only in specialization
        complete1 = orchestrator1._build_complete_system_message()
        complete2 = orchestrator2._build_complete_system_message()
        
        # Both should contain same behavior part
        behavior_part1 = complete1.split("Domain Specialization:")[0]
        behavior_part2 = complete2.split("Domain Specialization:")[0]
        assert behavior_part1 == behavior_part2
        
        # Specialization parts should differ
        spec_part1 = complete1.split("Domain Specialization:")[1]
        spec_part2 = complete2.split("Domain Specialization:")[1]
        assert spec_part1 != spec_part2
        assert "web scraping" in spec_part1
        assert "image processing" in spec_part2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

