# test/test_engine/test_crewai_builder.py

import pytest
from engine.crewai_builder import CrewAIBuilder
from graph.graph_plan import GraphPlan

class DummyAgent:
    def __call__(self, state):
        return state

def test_crewai_builds_flat_tasks():
    plan = GraphPlan()
    plan.add_step("agent_1", DummyAgent())
    plan.add_step("agent_2", DummyAgent())

    builder = CrewAIBuilder()
    crew = builder.build(plan)

    assert crew is not None
    assert hasattr(crew, "run")
    assert len(crew.tasks) == 2
    assert all("agent_" in task for task in crew.tasks)

def test_crewai_run_executes_all_tasks(capsys):
    plan = GraphPlan()
    plan.add_step("agent_1", DummyAgent())
    plan.add_step("agent_2", DummyAgent())

    builder = CrewAIBuilder()
    crew = builder.build(plan)
    crew.run()

    captured = capsys.readouterr()
    assert "Running task" in captured.out
