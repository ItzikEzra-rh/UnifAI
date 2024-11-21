import json

from g_eval.config import Config
from utils.celery.celery import send_task
from logger import logger

def main() -> None:
    """Main function to run the GEval-based evaluation system."""
    try:
        config = Config()

        # Load input data
        with config.INPUT_FILE_PATH.open('r') as f:
            elements = json.load(f)

        send_task(task_name="fetch_prompt_lab_generated_objects",
                  #data={'data': elements},
                  celery_queue='reviewer_queue',
                  data=elements)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()