# Agent System Edge Case Tests

This document describes the comprehensive edge case test suite designed to validate the robustness and reliability of the agent system under extreme conditions.

## 🎯 **Test Coverage Overview**

### **1. Parser Edge Cases** (`test_parser_edge_cases.py`)
Tests parser robustness with malformed and extreme inputs:

- **Large Content**: Up to 50KB limit (discovers actual parser limits)
- **Unicode Stress**: Emojis, international characters, symbols
- **Deep Nesting**: Complex nested data structures (5+ levels)
- **Boundary Conditions**: Up to 10 tool calls limit, extremely long names/IDs
- **Malformed Data**: Invalid JSON, wrong types, circular references
- **Concurrency**: Thread safety with concurrent parser usage
- **Memory Efficiency**: Large argument parsing without memory leaks

### **2. Agent System Edge Cases** (`test_agent_edge_cases.py`)
Tests complex agent workflows and failure scenarios:

- **Max Steps Boundary**: Behavior at step limits
- **Malformed LLM Responses**: Recovery from invalid responses
- **Concurrent Tool Execution**: Parallel tool calls with failures
- **Resource Exhaustion**: Memory pressure scenarios
- **Stateful Tool Corruption**: Tool state corruption and recovery
- **Cascading Failures**: Complex failure chains across multiple tools
- **Guided Mode Failures**: User confirmation with failing tools

### **3. Stress Tests** (`test_agent_stress.py`)
Tests system performance and race conditions:

- **Long Conversations**: 100+ message contexts
- **Rapid Fire Execution**: High-frequency tool calls
- **Concurrent Iterators**: Multiple agent instances running simultaneously
- **Parser Stress**: Large/malformed data processing
- **Memory Pressure**: Multiple iterators with large data
- **Timeout Handling**: Tool execution timeouts under load
- **Race Condition Detection**: Concurrent access to shared resources

## 🧪 **Test Tools and Utilities**

### **Specialized Test Tools**

1. **FlakySLowTool**: Simulates network issues and intermittent failures
   - Configurable failure rate (0-100%)
   - Simulated network delays
   - Random timeout/connection errors

2. **MemoryHogTool**: Tests memory consumption scenarios
   - Exponential memory growth
   - Memory allocation tracking
   - Resource exhaustion simulation

3. **StatefulTool**: Tests state management and corruption
   - Complex internal state
   - State corruption scenarios
   - Locking mechanisms

4. **RacyTool**: Tests thread safety and race conditions
   - Shared counter with race conditions
   - Optional locking mechanisms
   - Concurrent access patterns

5. **SlowTool**: Tests timeout handling
   - Configurable delays
   - Timeout simulation

6. **RandomResponseTool**: Tests parser with various response types
   - Large responses (10KB+)
   - Unicode stress responses
   - JSON/XML formatted responses

## 🚀 **Running Edge Case Tests**

### **Individual Test Suites**
```bash
# Parser edge cases
python -m pytest tests/unit/agent_system/parsers/test_parser_edge_cases.py -v

# Agent system edge cases
python -m pytest tests/integration/agent_workflows/test_agent_edge_cases.py -v

# Stress tests
python -m pytest tests/integration/agent_workflows/test_agent_stress.py -v
```

### **All Edge Cases**
```bash
# Run all edge case tests
python run_edge_case_tests.py

# With specific markers
python -m pytest -m "edge_cases or stress" -v

# With timeout protection
python -m pytest tests/integration/agent_workflows/ --timeout=300 -v
```

### **Performance Monitoring**
```bash
# With coverage and timing
python -m pytest tests/integration/agent_workflows/ --cov=elements/nodes/common/agent --durations=10 -v

# Memory profiling (requires memory_profiler)
python -m pytest tests/integration/agent_workflows/test_agent_stress.py::TestAgentStress::test_memory_pressure_simulation --profile-svg
```

## 🔍 **Discovered System Limits**

The edge case tests have revealed the actual system boundaries:

### **Parser Limits**
- **Maximum Content Length**: 50,000 characters
- **Maximum Tool Calls per Message**: 10 tool calls
- **Minimum Content Length**: Configurable (default varies)
- **Tool Name Validation**: Accepts most characters including spaces, dashes, underscores
- **Argument Nesting**: No practical limit on nested data structures
- **Unicode Support**: Full Unicode support including emojis and international characters

### **Agent System Limits**
- **Maximum Steps**: Configurable per strategy (default varies by strategy)
- **Concurrent Tool Execution**: Limited by ToolExecutorManager configuration
- **Memory Usage**: Bounded by tool implementations and message history
- **Timeout Handling**: Configurable per tool and execution context

### **Error Recovery Behavior**
- **Parse Errors**: Create ERROR steps that are terminal (stop execution)
- **Tool Failures**: Create failed observations but allow continuation
- **Resource Exhaustion**: Graceful degradation with error reporting
- **Malformed Responses**: Converted to ParseError with system feedback

## 📊 **Expected Behaviors**

### **Graceful Degradation**
- System should handle failures without crashing
- Partial success in multi-tool scenarios
- Proper error reporting and recovery

### **Resource Management**
- Memory usage should remain bounded
- Timeouts should be respected
- Concurrent operations should not deadlock

### **Error Handling**
- Parse errors should be recoverable
- Tool failures should not crash the system
- Invalid inputs should be rejected gracefully

### **Performance Characteristics**
- Concurrent operations should be faster than sequential
- Large inputs should not cause exponential slowdown
- System should handle 10+ concurrent agents

## 🔍 **Debugging Edge Cases**

### **Common Issues**
1. **Memory Leaks**: Monitor memory usage during long-running tests
2. **Race Conditions**: Look for inconsistent results in concurrent tests
3. **Deadlocks**: Tests that hang indefinitely
4. **Resource Exhaustion**: System becoming unresponsive

### **Debugging Commands**
```bash
# Run with detailed output
python -m pytest tests/integration/agent_workflows/test_agent_edge_cases.py -v -s

# Run specific failing test
python -m pytest tests/integration/agent_workflows/test_agent_edge_cases.py::TestAgentEdgeCases::test_complex_failure_cascade -v -s

# Run with pdb on failure
python -m pytest tests/integration/agent_workflows/test_agent_edge_cases.py --pdb

# Profile memory usage
python -m pytest tests/integration/agent_workflows/test_agent_stress.py::TestAgentStress::test_memory_pressure_simulation --profile
```

### **Monitoring Tools**
- **htop/top**: Monitor CPU and memory usage
- **pytest-monitor**: Track test performance over time
- **pytest-benchmark**: Benchmark critical paths
- **memory_profiler**: Profile memory usage patterns

## 🎯 **Success Criteria**

### **Robustness**
- ✅ All edge case tests pass
- ✅ No memory leaks detected
- ✅ No deadlocks or hangs
- ✅ Graceful error handling

### **Performance**
- ✅ Concurrent operations complete within 2x sequential time
- ✅ Large inputs (100KB+) processed within 5 seconds
- ✅ 10+ concurrent agents supported
- ✅ Memory usage remains bounded

### **Reliability**
- ✅ Consistent results across multiple runs
- ✅ No race conditions detected
- ✅ Proper cleanup after failures
- ✅ Error recovery mechanisms work

## 🔧 **Extending Edge Case Tests**

### **Adding New Edge Cases**
1. Identify failure scenarios in production
2. Create minimal reproduction cases
3. Add to appropriate test suite
4. Document expected behavior
5. Update this README

### **Test Categories**
- **Parser**: Input validation and malformed data
- **Agent**: Workflow and strategy edge cases
- **Stress**: Performance and concurrency
- **Integration**: End-to-end failure scenarios

### **Best Practices**
- Use realistic failure scenarios
- Test boundary conditions explicitly
- Include both positive and negative cases
- Document expected vs. actual behavior
- Use appropriate timeouts and resource limits

## 📈 **Continuous Improvement**

### **Monitoring**
- Track edge case test results over time
- Monitor performance regressions
- Identify new failure patterns
- Update tests based on production issues

### **Metrics**
- Test execution time trends
- Memory usage patterns
- Failure rate analysis
- Coverage of edge cases

This comprehensive edge case test suite ensures the agent system remains robust and reliable under all conditions! 🚀
