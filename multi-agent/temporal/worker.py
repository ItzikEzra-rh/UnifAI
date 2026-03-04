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
from engine.temporal.node_executor import NodeExecutor
from temporal.client import get_temporal_client
from temporal.activities import GraphNodeActivities
from temporal.workflow import GraphTraversalWorkflow


async def run_worker(threads: int) -> None:
    cfg = AppConfig.get_instance()
    container = AppContainer(cfg)

    node_executor = NodeExecutor(
        session_factory=container.session_factory,
    )
    activities = GraphNodeActivities(node_executor=node_executor)

    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=cfg.temporal_task_queue,
        workflows=[GraphTraversalWorkflow],
        activities=[
            activities.execute_node,
            activities.evaluate_condition,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=threads),
        max_concurrent_activities=threads,
        # Our workflow imports modules that use datetime.utcnow in Pydantic
        # field defaults. The sandbox blocks this even though the workflow
        # itself is deterministic. Safe to disable.
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
