import json
import asyncio

from g_eval.config import Config
from g_eval.system_async import AsyncGEvalSystem
from logger import logger

# def main() -> None:
#     """Main function to run the GEval-based evaluation system."""
#     try:
#         config = Config()
#         eval_system = GEvalQASystem(config)

#         # Load input data
#         with config.INPUT_FILE_PATH.open('r') as f:
#             elements = json.load(f)

#         # Process elements
#         eval_system.process_elements(elements)

#         # Save results
#         eval_system.save_results(eval_system.passed_elements, config.PASSED_FILE_PATH)
#         eval_system.save_results(eval_system.failed_elements, config.FAILED_FILE_PATH)

#         logger.info(
#             f"Evaluation complete. {len(eval_system.passed_elements)} elements passed and "
#             f"{len(eval_system.failed_elements)} elements failed."
#         )

#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         raise

async def file_detector_main() -> None:
    """Main async function to run the GEval-based evaluation system."""
    try:
        config = Config()
        async_eval_system = AsyncGEvalSystem(config)
        await async_eval_system.start_monitoring()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

###############################################################################################################################################

# import asyncio

# from g_eval.g_eval_qa_scoring_system import DeepEvalQASystem
# from g_eval.config import GEvalConfig

# async def deepeval_main() -> None:
#     """Main function to run the DeepEval-based evaluation system."""
#     try:
#         config = GEvalConfig()
#         eval_system = DeepEvalQASystem(config)

#         # Load input data
#         with config.INPUT_FILE_PATH.open('r') as f:
#             elements = json.load(f)

#         # Process elements
#         await eval_system.process_elements(elements)

#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         raise

###############################################################################################################################################

if __name__ == "__main__":
    asyncio.run(file_detector_main())
    # asyncio.run(deepeval_main())