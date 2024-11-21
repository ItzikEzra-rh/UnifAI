from celery_app.init import celery


def send_task(task_name, celery_queue, **kwargs):
    celery.send_task(f"celery_app.tasks.{task_name}",
                     kwargs=kwargs,
                     queue=celery_queue)


def is_celery_queue_empty(queue_name: str) -> bool:
    """
    Checks if a given Celery queue is empty by inspecting both reserved and scheduled tasks.

    Args:
        queue_name (str): Name of the queue to check.

    Returns:
        bool: True if the queue is empty, False otherwise.
    """
    inspect = celery.control.inspect()
    # Check reserved tasks
    reserved_tasks = inspect.reserved()

    if reserved_tasks:
        for worker, tasks in reserved_tasks.items():
            for task in tasks:
                if task.get('delivery_info', {}).get('routing_key') == queue_name:
                    print(f"Queue '{queue_name}' is not empty. Found reserved task: {task['name']}")
                    return False
    return True
