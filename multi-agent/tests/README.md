# Multi-Agent System Test Suite

Professional test structure organized by system components and testing levels.

## 🏗️ Test Structure

```
tests/
├── unit/                           # Unit tests (isolated component testing)
│   ├── agent_system/              # Agent reasoning and execution system
│   │   ├── strategies/            # Decision-making strategies (ReAct, Plan&Execute)
│   │   ├── execution/             # Execution flow (Iterator, Executor, Actions)
│   │   ├── parsers/               # Output parsing (ToolCall, Text, JSON parsers)
│   │   └── primitives/            # Core data structures (AgentAction, AgentStep, etc.)
│   ├── llm_integration/           # LLM provider integrations
│   │   ├── providers/             # OpenAI, Anthropic, local models
│   │   ├── message_handling/      # Chat message conversion and validation
│   │   └── streaming/             # Real-time response streaming
│   ├── tool_execution/            # Tool management and execution
│   │   ├── framework/             # ToolExecutorManager, execution modes
│   │   ├── providers/             # MCP, SSH, custom tool providers
│   │   └── validation/            # Argument validation, security policies
│   ├── graph_engine/              # Workflow graph execution
│   │   ├── builders/              # Graph construction and validation
│   │   ├── execution/             # Graph traversal and state management
│   │   └── validation/            # Graph validation and optimization
│   └── session_management/        # User sessions and state persistence
│       ├── lifecycle/             # Session creation, updates, cleanup
│       ├── persistence/           # MongoDB, file-based storage
│       └── sharing/               # Session sharing and collaboration
├── integration/                    # Multi-component integration tests
│   ├── agent_workflows/           # Complete agent execution flows
│   │   ├── react_flows/           # ReAct strategy end-to-end
│   │   ├── plan_execute_flows/    # Plan&Execute strategy workflows
│   │   └── custom_workflows/      # Custom agent implementations
│   ├── multi_component/           # Cross-system component testing
│   │   ├── agent_tool_integration/# Agent + Tool execution integration
│   │   ├── llm_agent_integration/ # LLM + Agent strategy integration
│   │   └── graph_session_integration/ # Graph + Session management
│   └── error_scenarios/           # Error handling and recovery
│       ├── network_failures/      # Network timeouts, connectivity issues
│       ├── llm_failures/          # LLM API failures, rate limits
│       └── tool_failures/         # Tool execution errors, validation failures
├── e2e/                           # End-to-end system tests
│   ├── complete_scenarios/        # Full user scenarios
│   │   ├── research_tasks/        # Information gathering workflows
│   │   ├── automation_tasks/      # Task automation scenarios
│   │   └── collaboration_tasks/   # Multi-user collaboration
│   └── performance/               # Performance and load testing
│       ├── throughput/            # Request handling capacity
│       ├── latency/               # Response time measurements
│       └── resource_usage/        # Memory, CPU, storage usage
├── fixtures/                      # Test data and mock objects
│   ├── agent_data/               # Sample agent configurations, messages
│   ├── llm_responses/            # Mock LLM responses for different scenarios
│   ├── tool_data/                # Sample tool definitions and responses
│   └── graph_data/               # Sample workflow graphs and states
├── utils/                         # Test utilities and helpers
│   ├── mocks/                    # Reusable mock objects and factories
│   ├── assertions/               # Custom assertion helpers
│   └── generators/               # Test data generators
├── conftest.py                   # Global test configuration and fixtures
└── pytest.ini                   # Pytest configuration
```

## 🎯 Testing Philosophy

### **Component-Based Organization**
Tests are organized by **system components** rather than source code structure:
- **Agent System**: Core reasoning and execution logic
- **LLM Integration**: Language model interactions
- **Tool Execution**: Tool management and execution framework
- **Graph Engine**: Workflow orchestration
- **Session Management**: User state and persistence

### **Testing Levels**
1. **Unit Tests**: Isolated component testing with mocked dependencies
2. **Integration Tests**: Multi-component interactions and workflows
3. **E2E Tests**: Complete user scenarios and system validation

## 📋 Current Test Coverage

### ✅ **Implemented (Agent System)**
- `unit/agent_system/strategies/` - ReAct strategy testing
- `unit/agent_system/execution/` - Iterator and executor testing
- `unit/agent_system/parsers/` - Output parser testing
- `integration/agent_workflows/react_flows/` - Complete ReAct workflows

### 🔄 **Ready for Implementation**
- `unit/agent_system/primitives/` - Core data structures
- `unit/llm_integration/` - LLM provider testing
- `unit/tool_execution/` - Tool framework testing
- `unit/graph_engine/` - Graph execution testing
- `unit/session_management/` - Session lifecycle testing

## 🚀 Running Tests

### **By Component**
```bash
# Agent system tests
pytest tests/unit/agent_system/ -v

# LLM integration tests  
pytest tests/unit/llm_integration/ -v

# Tool execution tests
pytest tests/unit/tool_execution/ -v
```

### **By Test Level**
```bash
# All unit tests
pytest tests/unit/ -v

# All integration tests
pytest tests/integration/ -v

# All end-to-end tests
pytest tests/e2e/ -v
```

### **Specific Components**
```bash
# ReAct strategy tests
pytest tests/unit/agent_system/strategies/ -k "react" -v

# Tool execution framework
pytest tests/unit/tool_execution/framework/ -v

# Complete agent workflows
pytest tests/integration/agent_workflows/ -v
```

## 📝 Test Naming Conventions

### **File Naming**
- `test_<component_name>.py` - Main component tests
- `test_<component>_<specific_feature>.py` - Feature-specific tests
- `test_<scenario_name>_workflow.py` - Integration/E2E workflow tests

### **Class Naming**
- `TestComponentName` - Main test class
- `TestComponentNameFeature` - Feature-specific test class
- `TestWorkflowName` - Workflow test class

### **Method Naming**
- `test_<behavior>` - Standard test method
- `test_<behavior>_when_<condition>` - Conditional behavior
- `test_<behavior>_should_<expected_result>` - Expected outcome

## 🔧 Adding New Tests

### **For New Components**
1. Create directory under appropriate test level
2. Add component-specific subdirectories if needed
3. Create `__init__.py` files for proper imports
4. Add fixtures to `conftest.py` if reusable

### **Example: Adding Graph Engine Tests**
```bash
# Create test structure
mkdir -p tests/unit/graph_engine/{builders,execution,validation}

# Create test files
touch tests/unit/graph_engine/builders/test_graph_builder.py
touch tests/unit/graph_engine/execution/test_graph_executor.py
touch tests/unit/graph_engine/validation/test_graph_validator.py

# Add integration tests
mkdir -p tests/integration/multi_component/graph_session_integration
touch tests/integration/multi_component/graph_session_integration/test_graph_session_workflow.py
```

## 🏷️ Test Markers

Use pytest markers for categorization:

```python
@pytest.mark.unit
@pytest.mark.agent_system
def test_react_strategy():
    pass

@pytest.mark.integration  
@pytest.mark.agent_workflows
def test_complete_react_flow():
    pass

@pytest.mark.e2e
@pytest.mark.slow
def test_full_research_scenario():
    pass
```

Available markers:
- **Level**: `unit`, `integration`, `e2e`
- **Component**: `agent_system`, `llm_integration`, `tool_execution`, `graph_engine`, `session_management`
- **Speed**: `fast`, `slow`
- **Stability**: `stable`, `flaky`

## 📊 Test Quality Standards

### **Unit Tests**
- ✅ Fast execution (< 1s per test)
- ✅ Isolated with mocked dependencies
- ✅ Single responsibility per test
- ✅ Clear arrange-act-assert structure

### **Integration Tests**
- ✅ Test real component interactions
- ✅ Moderate execution time (< 10s per test)
- ✅ Realistic data and scenarios
- ✅ Error path coverage

### **E2E Tests**
- ✅ Complete user scenarios
- ✅ Real system interactions
- ✅ Performance validation
- ✅ Acceptance criteria verification

## 🔍 Debugging and Maintenance

### **Test Debugging**
```bash
# Run with debugger
pytest --pdb tests/unit/agent_system/strategies/test_react_strategy.py

# Verbose output with logging
pytest -v -s --log-cli-level=DEBUG

# Run specific test with full output
pytest tests/unit/agent_system/strategies/test_react_strategy.py::TestReActStrategy::test_multiple_tool_calls -v -s
```

### **Test Maintenance**
- Regular review of test coverage
- Update tests when components change
- Remove obsolete tests
- Refactor common patterns into fixtures

This structure ensures **scalable, maintainable, and professional** test coverage for the entire multi-agent system! 🎉