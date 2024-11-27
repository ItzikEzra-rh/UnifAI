import json

from g_eval.config import Config
from reviewer.g_eval.qa_scoring_system import GEvalQASystem
from reviewer.g_eval.system_async import AsyncGEvalSystem
from utils.celery.celery import send_task
from logger import logger


async def process_elements(elements):
    try: 
        await eval_system.process_elements(elements)

        send_task(task_name="process_passed_prompts",
                  data=eval_system.passed_elements,
                  celery_queue='reviewer_passed')

        # send_task(task_name="fetch_reviewer_failed_generated_objects",
        #           data=self.failed_elements,
        #           celery_queue='reviewer_fail_queue')
        
        logger.info(
            f"Evaluation complete. {len(eval_system.passed_elements)} elements passed and "
            f"{len(eval_system.failed_elements)} elements failed."
        )
        eval_system.passed_elements = []
        eval_system.failed_elements = []
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

def save_elements(elements):
    # Save results
    eval_system.save_results(elements, config.PASSED_FILE_PATH)
    # eval_system.save_results(eval_system.failed_elements, config.FAILED_FILE_PATH)


config = Config()
eval_system = GEvalQASystem(config)