import logging
from celery_app.init import celery
from processing.factory import DataProcessorFactory
from utils.celery.celery import send_task


@celery.task()
def fetch_prompts_batch(batch):
    formatted_prompt = [element["formatted_prompt"] for element in batch]
    metadata = [element["metadata"] for element in batch]
    data_processor = DataProcessorFactory().create()
    res_batch = data_processor.process_batch(batch_prompts=formatted_prompt, metadata=metadata)
    send_task(task_name="fetch_prompt_lab_generated_objects",
              celery_queue="reviewer_queue",
              data=res_batch)


@celery.task()
def process_passed_prompts(data):
    data_processor = DataProcessorFactory().create()
    for prompt in data:
        data_processor.save_processed_prompt(prompt)
