import json

from g_eval.config import Config
from g_eval.g_eval_qa_scoring_system import GEvalQASystem
from g_eval.g_eval_system_async import AsyncGEvalSystem
from logger import logger


def process_elements(elements):
    try: 
        eval_system.process_elements(elements)
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
    pass
    # Save results
    # eval_system.save_results(eval_system.passed_elements, config.PASSED_FILE_PATH)
    # eval_system.save_results(eval_system.failed_elements, config.FAILED_FILE_PATH)


config = Config()
eval_system = GEvalQASystem(config)