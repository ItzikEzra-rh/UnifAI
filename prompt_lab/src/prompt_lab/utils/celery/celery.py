from celery_app.init import celery
from kombu import Connection
from utils.util import get_rabbitmq_url
import time


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


def get_queue_length_rabbitmq(queue_name):
    with Connection(get_rabbitmq_url()) as conn:
        queue = conn.SimpleQueue(queue_name)
        return queue.qsize()


def is_queue_full(queue_name, queue_target_size, max_retries=3, retry_delay=5) -> bool:
    """
    Check if the RabbitMQ queue is full with retry mechanism.

    Args:
        queue_name (str): The name of the RabbitMQ queue.
        queue_target_size (int): The maximum allowed size of the queue.
        max_retries (int): The maximum number of retries before failing.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        bool: True if the queue is full, False otherwise.

    Raises:
        Exception: If retries are exhausted and the operation fails.
    """
    retries = 0

    while retries <= max_retries:
        try:
            queue_length = get_queue_length_rabbitmq(queue_name)
            return queue_length >= queue_target_size
        except Exception as e:
            retries += 1
            print(f"[Orchestrator] Error checking queue length (attempt {retries}/{max_retries}): {e}")
            if retries > max_retries:
                print("[Orchestrator] Max retries reached. Failing.")
                raise  # Re-raise the last exception
            time.sleep(retry_delay)
