# 🧪 COMPREHENSIVE ORCHESTRATOR TEST PLAN

## 📋 OVERVIEW

This document outlines the complete testing strategy for the orchestrator node after our major refactoring. The tests cover all components, integration scenarios, edge cases, and end-to-end workflows.

## 🎯 TESTING SCOPE

### **Changes That Need Testing:**
1. **Pydantic Models**: `WorkItem`, `WorkPlan`, `WorkItemResult`, `ToolArguments`, etc.
2. **Dependencies**: `WorkItem.dependencies`, `is_ready_for_execution()`, `is_blocked()`
3. **Tool Schemas**: Improved `CreateOrUpdateWorkPlanTool`, `DelegateTaskTool` schemas
4. **Status Management**: `mark_item_as_delegated()`, `ingest_task_response()`
5. **System Messages**: Separated domain vs orchestrator behavior
6. **Phase Tool Filtering**: Removed `MarkWorkItemStatusTool` from LLM access
7. **Batch Processing**: Updated packet handling
8. **Context Building**: Improved `_build_plan_snapshot()`

---

## 🏗️ TEST STRUCTURE

### **Unit Tests** (`tests/unit/`)

#### **1. Workload Layer** (`tests/unit/workload/`)
- ✅ `test_workplan.py` - Updated for Pydantic changes
- ✅ `test_workplan_pydantic.py` - New comprehensive Pydantic model tests
- ✅ `test_delegation_status.py` - New delegation status management tests

#### **2. Tool Layer** (`tests/unit/tools/`)
- ✅ `test_improved_tool_schemas.py` - New tool schema validation tests

#### **3. Agent Layer** (`tests/unit/nodes/common/agent/`)
- ✅ `test_phase_protocols.py` - Updated for new protocols
- ✅ `test_phase_tools.py` - Updated for removed MarkWorkItemStatusTool

#### **4. Orchestrator Layer** (`tests/unit/nodes/orchestrator/`)
- ✅ `test_orchestrator_phase_transitions.py` - Updated for Pydantic models
- 🔄 `test_orchestrator_system_messages.py` - **NEW** - System message separation
- 🔄 `test_orchestrator_batch_processing.py` - **NEW** - Batch packet handling
- 🔄 `test_orchestrator_context_building.py` - **NEW** - Plan snapshot improvements

### **Integration Tests** (`tests/integration/`)

#### **5. Orchestrator Integration** (`tests/integration/orchestrator/`)
- 🔄 `test_orchestrator_full_workflow.py` - **NEW** - Complete orchestration cycles
- 🔄 `test_orchestrator_delegation_flow.py` - **NEW** - Delegation with status updates
- 🔄 `test_orchestrator_dependency_handling.py` - **NEW** - Dependency resolution
- 🔄 `test_orchestrator_error_scenarios.py` - **NEW** - Error handling and recovery

### **End-to-End Tests** (`tests/e2e/`)

#### **6. Complete Scenarios** (`tests/e2e/orchestrator/`)
- 🔄 `test_e2e_simple_orchestration.py` - **NEW** - Basic orchestration scenario
- 🔄 `test_e2e_complex_dependencies.py` - **NEW** - Multi-level dependencies
- 🔄 `test_e2e_mixed_local_remote.py` - **NEW** - Local + remote execution
- 🔄 `test_e2e_error_recovery.py` - **NEW** - Error handling and retry

---

## 🧪 DETAILED TEST CASES

### **A. Pydantic Model Tests**

#### **WorkItem Model**
```python
def test_work_item_validation():
    """Test Pydantic validation for WorkItem."""
    # Valid creation
    item = WorkItem(id="test", title="Test", description="Test task")
    
    # Invalid enum values should fail
    with pytest.raises(ValidationError):
        WorkItem(id="test", title="Test", description="Test", status="invalid")

def test_work_item_dependencies():
    """Test dependency logic."""
    item = WorkItem(id="task2", title="Task 2", description="Depends on task1", 
                   dependencies=["task1"])
    
    assert not item.is_ready_for_execution(set())
    assert item.is_ready_for_execution({"task1"})
    assert item.is_blocked(set())
```

#### **WorkPlan Model**
```python
def test_work_plan_ready_items():
    """Test getting ready items with dependencies."""
    plan = WorkPlan(summary="Test", owner_uid="test", thread_id="test")
    
    # Add items with dependencies
    item1 = WorkItem(id="item1", title="Task 1", description="First")
    item2 = WorkItem(id="item2", title="Task 2", description="Second", 
                    dependencies=["item1"])
    
    plan.items = {"item1": item1, "item2": item2}
    
    # Only item1 should be ready initially
    ready = plan.get_ready_items()
    assert len(ready) == 1
    assert ready[0].id == "item1"
```

### **B. Tool Schema Tests**

#### **CreateOrUpdateWorkPlanTool**
```python
def test_improved_work_item_spec():
    """Test improved WorkItemSpec schema."""
    spec = WorkItemSpec(
        id="analyze_data",
        title="Analyze Sales Data", 
        description="Extract Q4 metrics",
        dependencies=["extract_data"],
        kind=WorkItemKind.REMOTE,
        estimated_duration="2 hours"
    )
    
    assert spec.id == "analyze_data"
    assert spec.dependencies == ["extract_data"]
    assert spec.kind == WorkItemKind.REMOTE

def test_plan_args_validation():
    """Test plan arguments validation."""
    # Empty items should fail (min_items=1)
    with pytest.raises(ValidationError):
        CreateOrUpdatePlanArgs(summary="Test", items=[])
```

#### **DelegateTaskTool**
```python
def test_delegate_args_descriptions():
    """Test helpful field descriptions."""
    dst_uid_field = DelegateTaskArgs.model_fields['dst_uid']
    assert 'ListAdjacentNodesTool' in dst_uid_field.description
    
    content_field = DelegateTaskArgs.model_fields['content']
    assert 'detailed' in content_field.description.lower()
```

### **C. Delegation Status Tests**

#### **Status Update Flow**
```python
def test_delegation_workflow():
    """Test complete delegation workflow."""
    service = WorkPlanService(workspace)
    
    # 1. Create plan with pending item
    plan = create_sample_plan()
    service.save(plan)
    
    # 2. Mark as delegated (PENDING → WAITING)
    success = service.mark_item_as_delegated("owner", "item1", "task-123")
    assert success
    
    plan = service.load("owner")
    assert plan.items["item1"].status == WorkItemStatus.WAITING
    
    # 3. Ingest response (WAITING → DONE)
    success = service.ingest_task_response("owner", "task-123", result="success")
    assert success
    
    plan = service.load("owner")
    assert plan.items["item1"].status == WorkItemStatus.DONE
```

### **D. Phase Transition Tests**

#### **Updated Phase Logic**
```python
def test_phase_transitions_with_dependencies():
    """Test phase transitions consider dependencies."""
    policy = OrchestratorPhaseTransitionPolicy()
    
    # Plan with blocked items should go to MONITORING
    state = create_phase_state(
        work_plan_status=create_work_plan_status(
            total_items=2,
            pending_items=1,  # But blocked by dependencies
            blocked_items=1
        )
    )
    
    phase = policy.decide(state=state, current=ExecutionPhase.ALLOCATION, observations=[])
    assert phase == ExecutionPhase.MONITORING  # Wait for dependencies
```

### **E. System Message Tests**

#### **Message Separation**
```python
def test_system_message_separation():
    """Test separated domain vs orchestrator messages."""
    node = OrchestratorNode(
        llm=mock_llm,
        system_message="I specialize in document analysis"
    )
    
    complete_message = node._build_complete_system_message()
    
    # Should contain both orchestrator behavior and domain specialization
    assert "orchestrator agent" in complete_message.lower()
    assert "document analysis" in complete_message
    assert "Domain Specialization:" in complete_message

def test_orchestrator_behavior_message_fixed():
    """Test that orchestrator behavior message is consistent."""
    msg = OrchestratorNode._get_orchestrator_behavior_message()
    
    assert "coordinate work execution" in msg.lower()
    assert "work plans" in msg.lower()
    assert "delegate" in msg.lower()
```

### **F. Batch Processing Tests**

#### **Packet Handling**
```python
def test_batch_packet_processing():
    """Test batch processing of multiple packets."""
    node = OrchestratorNode(llm=mock_llm)
    
    # Create multiple response packets
    packets = [
        create_response_packet("task-1", "result-1"),
        create_response_packet("task-2", "result-2"),
        create_response_packet("task-3", "result-3")
    ]
    
    # Mock inbox to return packets
    node.inbox_packets = Mock(return_value=packets)
    
    # Process batch
    node.process_packets_batched(mock_state)
    
    # Should process all packets and run orchestration once per thread
    assert len(node._updated_threads) > 0
```

### **G. Context Building Tests**

#### **Plan Snapshot**
```python
def test_improved_plan_snapshot():
    """Test improved plan snapshot with dependencies."""
    node = OrchestratorNode(llm=mock_llm)
    
    # Create plan with various statuses and dependencies
    setup_plan_with_dependencies(node, "thread-123")
    
    snapshot = node._build_plan_snapshot("thread-123")
    
    # Should include dependency information
    assert "[depends on:" in snapshot
    assert "[assigned to:" in snapshot
    assert "WAITING" in snapshot
    assert "DONE" in snapshot
```

### **H. Error Scenario Tests**

#### **Edge Cases**
```python
def test_delegation_with_invalid_correlation():
    """Test handling invalid correlation IDs."""
    service = WorkPlanService(workspace)
    
    success = service.ingest_task_response(
        owner_uid="owner",
        correlation_task_id="nonexistent",
        result="data"
    )
    
    assert success is False

def test_circular_dependencies():
    """Test handling circular dependencies."""
    item1 = WorkItem(id="item1", title="Task 1", description="First", 
                    dependencies=["item2"])
    item2 = WorkItem(id="item2", title="Task 2", description="Second",
                    dependencies=["item1"])
    
    plan = WorkPlan(summary="Circular", owner_uid="test", thread_id="test",
                   items={"item1": item1, "item2": item2})
    
    # Should detect circular dependency
    ready_items = plan.get_ready_items()
    assert len(ready_items) == 0  # Nothing can be ready
    
    blocked_items = plan.get_blocked_items()
    assert len(blocked_items) == 2  # Both are blocked
```

---

## 🎯 END-TO-END SCENARIOS

### **Scenario 1: Simple Orchestration**
```
1. User: "Analyze Q4 sales data and create presentation"
2. Orchestrator creates 2-item plan with dependencies
3. Delegates data analysis to data_analyst_node
4. Receives analysis results
5. Delegates presentation creation to presentation_node
6. Receives presentation
7. Synthesizes final summary
```

### **Scenario 2: Complex Dependencies**
```
1. User: "Process customer data pipeline"
2. Orchestrator creates 5-item plan:
   - extract_data (no deps)
   - clean_data (depends on extract_data)
   - analyze_data (depends on clean_data)
   - generate_report (depends on analyze_data)
   - send_report (depends on generate_report)
3. Items execute in correct dependency order
4. Handles partial failures gracefully
```

### **Scenario 3: Mixed Local/Remote**
```
1. Plan includes both LOCAL and REMOTE items
2. LOCAL items execute without delegation
3. REMOTE items delegate to appropriate nodes
4. Dependencies work across local/remote boundaries
5. Final synthesis combines all results
```

### **Scenario 4: Error Recovery**
```
1. Delegation fails (node not adjacent)
2. Remote task fails with error
3. Dependency chain is broken
4. Orchestrator handles gracefully
5. Reports partial completion with errors
```

---

## 🚀 RUNNING THE TESTS

### **Prerequisites**
```bash
cd multi-agent
pip install pytest pytest-mock pydantic
```

### **Run Specific Test Suites**
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Workload layer tests
python -m pytest tests/unit/workload/ -v

# Tool schema tests  
python -m pytest tests/unit/tools/ -v

# Orchestrator tests
python -m pytest tests/unit/nodes/orchestrator/ -v

# Integration tests
python -m pytest tests/integration/ -v

# End-to-end tests
python -m pytest tests/e2e/ -v

# All orchestrator-related tests
python -m pytest -k "orchestrator" -v
```

### **Test Coverage**
```bash
# Run with coverage
python -m pytest --cov=elements.nodes.orchestrator --cov=elements.nodes.common.workload --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## ✅ TEST COMPLETION STATUS

### **Completed ✅**
- [x] Updated existing workplan tests for Pydantic
- [x] Created comprehensive Pydantic model tests
- [x] Created tool schema validation tests
- [x] Created delegation status management tests
- [x] Updated phase transition tests

### **In Progress 🔄**
- [ ] System message separation tests
- [ ] Batch processing tests
- [ ] Context building tests
- [ ] Full orchestrator integration tests
- [ ] Error scenario tests
- [ ] End-to-end workflow tests

### **Pending 📋**
- [ ] Performance tests
- [ ] Stress tests
- [ ] Chaos tests
- [ ] Security tests

---

## 🎯 SUCCESS CRITERIA

### **Unit Tests**
- ✅ All Pydantic models validate correctly
- ✅ Tool schemas provide helpful validation
- ✅ Delegation status updates work correctly
- ✅ Phase transitions handle new logic

### **Integration Tests**
- 🔄 Complete orchestration cycles work end-to-end
- 🔄 Dependencies are resolved correctly
- 🔄 Batch processing improves performance
- 🔄 Error handling is robust

### **End-to-End Tests**
- 🔄 Real-world scenarios complete successfully
- 🔄 Complex dependency chains work
- 🔄 Mixed local/remote execution works
- 🔄 Error recovery is graceful

### **Quality Metrics**
- 🎯 **Test Coverage**: >90% for orchestrator components
- 🎯 **Performance**: Batch processing 3-5x faster than sequential
- 🎯 **Reliability**: <1% failure rate in normal scenarios
- 🎯 **Maintainability**: Clear, readable test code

---

## 📝 NOTES

1. **Test Data**: Use consistent test data across all test files
2. **Mocking**: Mock external dependencies (LLM, IEM, etc.) consistently
3. **Fixtures**: Reuse common fixtures across test files
4. **Documentation**: Each test should have clear docstrings
5. **Performance**: Include performance benchmarks for critical paths

This comprehensive test plan ensures that all aspects of the orchestrator refactoring are thoroughly validated and that the system works reliably in production scenarios.

