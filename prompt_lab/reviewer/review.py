
import json
from qa_scoring_system import QAScoringSystem
from config import Config
from logger import logger

def main() -> None:
    """Main function to run the Q&A scoring system."""
    try:
        config = Config()
        qa_system = QAScoringSystem(config)

        # Load input data
        with config.INPUT_FILE_PATH.open('r') as f:
            elements = json.load(f)

        # Process elements
        qa_system.process_elements(elements)

        # Save results
        qa_system.save_results(qa_system.passed_elements, config.PASSED_FILE_PATH)
        qa_system.save_results(qa_system.failed_elements, config.FAILED_FILE_PATH)

        logger.info(
            f"Processing complete. {len(qa_system.passed_elements)} elements passed and "
            f"{len(qa_system.failed_elements)} elements failed."
        )

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()