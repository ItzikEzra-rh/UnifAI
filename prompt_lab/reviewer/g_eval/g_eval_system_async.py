import json
import asyncio
import time
from typing import Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from g_eval.config import Config
from g_eval.g_eval_qa_scoring_system import GEvalQASystem
from logger import logger

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, callback, loop):
        self.callback = callback
        self.loop = loop
        self.last_modified = 0
        self.processing_lock = asyncio.Lock()
        
    def on_modified(self, event):
        if not isinstance(event, FileModifiedEvent):
            return
            
        current_time = time.time()
        if current_time - self.last_modified > 0.5:  # Debounce modifications
            self.last_modified = current_time
            asyncio.run_coroutine_threadsafe(self.callback(), self.loop)

class AsyncGEvalSystem:
    def __init__(self, config: Config):
        self.config = config
        self.eval_system = GEvalQASystem(config)
        self.processed_elements: Set[str] = set()  # Store unique IDs of processed elements
        self.observer = None
        self.last_activity = time.time()
        self.is_running = False
        self.loop = None
        
    async def start_monitoring(self):
        """Start monitoring the input file for changes."""
        self.is_running = True
        self.loop = asyncio.get_running_loop()
        
        # Process existing file content first
        await self.process_initial_content()
        
        # Start file monitoring
        self.observer = Observer()
        event_handler = FileChangeHandler(self.handle_file_change, self.loop)
        self.observer.schedule(event_handler, str(self.config.INPUT_FILE_PATH.parent), recursive=False)
        self.observer.start()
        
        try:
            while self.is_running:
                current_time = time.time()
                if current_time - self.last_activity > 60:  # 1-minute timeout
                    logger.info("No new data for 1 minute, stopping monitoring")
                    await self.stop_monitoring()
                    break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await self.stop_monitoring()
            raise

    async def process_initial_content(self):
        """Process the initial content of the file if it exists."""
        try:
            if self.config.INPUT_FILE_PATH.exists():
                with self.config.INPUT_FILE_PATH.open('r') as f:
                    elements = json.load(f)
                if elements:
                    logger.info(f"Processing initial content with {len(elements)} elements")
                    await self.process_elements(elements)
                    self.last_activity = time.time()
        except Exception as e:
            logger.error(f"Error processing initial content: {e}")

    async def stop_monitoring(self):
        """Stop monitoring and cleanup."""
        self.is_running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Save final results
        self.eval_system.save_results(self.eval_system.passed_elements, self.config.PASSED_FILE_PATH)
        self.eval_system.save_results(self.eval_system.failed_elements, self.config.FAILED_FILE_PATH)
        
        logger.info(
            f"Final evaluation complete. {len(self.eval_system.passed_elements)} elements passed and "
            f"{len(self.eval_system.failed_elements)} elements failed."
        )

    async def handle_file_change(self):
        """Handle changes to the input file."""
        self.last_activity = time.time()
        
        try:
            # Read the file with retry mechanism
            for attempt in range(3):
                try:
                    with self.config.INPUT_FILE_PATH.open('r') as f:
                        elements = json.load(f)
                    break
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(0.5)
            
            # Process only new elements
            new_elements = [
                elem for elem in elements 
                if elem.get('id') not in self.processed_elements
            ]
            
            if new_elements:
                await self.eval_system.process_elements(new_elements, self.processed_elements)
                
        except Exception as e:
            logger.error(f"Error handling file change: {e}")

"""
Here is a detailed overviwe of the main functionality provided by the following class: 
- File Monitoring:
    1) Using watchdog to monitor file changes
    2) Implements debouncing to prevent multiple triggers for the same write
    3) Handles file access conflicts with retry mechanism

- Async Processing:
    1) Converts the main processing loop to async
    2) Implements proper cleanup on shutdown
    3) Uses asyncio for non-blocking operations

- Deduplication:
    1) Tracks processed elements using their IDs
    2) Only processes new elements when file changes occur

- Timeout Handling:
    1) Implements 1-minute inactivity timeout
    2) Gracefully stops monitoring and saves results

- Error Handling:
    1) Robust error handling throughout the pipeline
    2) Retries for file access issues
    3) Proper cleanup on errors
"""