"""
Temporal worker — inbound adapter.

Receives a fully-wired AppContainer from its entry point
(__main__.py) and uses it to build activity instances.
This adapter never creates the container itself.

Run as a standalone process:
    python -m inbound.temporal
    python -m inbound.temporal --threads 20

Multiple workers can run concurrently for horizontal scaling.
"""
from concurrent.futures import ThreadPoolExecutor

from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from mas.config.app_config import AppConfig
from mas.engine.distributed.node_executor import NodeExecutor
from mas.session.execution.lifecycle_handler import BackgroundLifecycleHandler
from mas.session.execution.lifecycle import SessionLifecycle
from temporal.client import get_temporal_client
from inbound.temporal.activities import GraphNodeActivities, SessionLifecycleActivities
from inbound.temporal.workflows import GraphTraversalWorkflow, SessionWorkflow


async def run_worker(container, threads: int) -> None:
    cfg = AppConfig.get_instance()

    node_executor = NodeExecutor(
        session_factory=container.session_factory,
    )

    graph_activities = GraphNodeActivities(
        node_executor=node_executor,
        channel_factory=container.channel_factory,
    )

    lifecycle = SessionLifecycle(repository=container.session_repo)
    lifecycle_handler = BackgroundLifecycleHandler(
        session_manager=container.session_manager,
        lifecycle=lifecycle,
        channel_factory=container.channel_factory,
    )
    lifecycle_activities = SessionLifecycleActivities(
        handler=lifecycle_handler,
    )

    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=cfg.temporal_task_queue,
        workflows=[GraphTraversalWorkflow, SessionWorkflow],
        activities=[
            graph_activities.execute_node,
            graph_activities.evaluate_condition,
            lifecycle_activities.begin_session,
            lifecycle_activities.complete_session,
            lifecycle_activities.fail_session,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=threads),
        max_concurrent_activities=threads,
        workflow_runner=UnsandboxedWorkflowRunner(),
    )

    print(f"Worker started | task_queue={cfg.temporal_task_queue} | threads={threads}")
    await worker.run()
