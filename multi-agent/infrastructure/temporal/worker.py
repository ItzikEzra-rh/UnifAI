"""
Temporal worker for the graph engine.

Run as a standalone process:
    python -m temporal.worker
    python -m temporal.worker --threads 20

Multiple workers can run concurrently for horizontal scaling.
"""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from config.app_config import AppConfig
from core.app_container import AppContainer
from engine.distributed.node_executor import NodeExecutor
from session.lifecycle import SessionLifecycle
from infrastructure.temporal.client import get_temporal_client
from infrastructure.temporal.activities import GraphNodeActivities, SessionLifecycleActivities
from infrastructure.temporal.workflow import GraphTraversalWorkflow
from infrastructure.temporal.session_workflow import SessionWorkflow


async def run_worker(threads: int) -> None:
    cfg = AppConfig.get_instance()
    container = AppContainer(cfg)

    node_executor = NodeExecutor(
        session_factory=container.session_factory,
    )
    graph_activities = GraphNodeActivities(node_executor=node_executor)

    lifecycle = SessionLifecycle(repository=container.session_repo)
    lifecycle_activities = SessionLifecycleActivities(
        session_manager=container.session_manager,
        lifecycle=lifecycle,
    )

    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=cfg.temporal_task_queue,
        workflows=[GraphTraversalWorkflow, SessionWorkflow],
        activities=[
            graph_activities.execute_node,
            graph_activities.evaluate_condition,
            lifecycle_activities.prepare_session,
            lifecycle_activities.complete_session,
            lifecycle_activities.fail_session,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=threads),
        max_concurrent_activities=threads,
        workflow_runner=UnsandboxedWorkflowRunner(),
    )

    print(f"Worker started | task_queue={cfg.temporal_task_queue} | threads={threads}")
    await worker.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Temporal graph engine worker")
    parser.add_argument("--threads", type=int, default=10, help="Activity thread pool size")
    args = parser.parse_args()

    asyncio.run(run_worker(args.threads))


if __name__ == "__main__":
    main()
