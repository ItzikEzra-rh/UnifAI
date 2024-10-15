import json
import os
import subprocess
from flask import Flask, request, jsonify
from abc import ABC, abstractmethod
from unsloth import FastLanguageModel
from transformers import TextStreamer, TextIteratorStreamer
from pathlib import Path
from be_utils.utils import find_latest_checkpoint
from threading import Thread, Event
import torch
from llm.hugging_face import HFTokenManager

app = Flask(__name__)

# Global variable to hold the model and tokenizer
model_loader = None
from transformers import StoppingCriteriaList
from transformers import StoppingCriteria


class CustomStoppingCriteria(StoppingCriteria):
    def __init__(self, stop_event):
        self.stop_event = stop_event

    def __call__(self, input_ids, scores):
        # Check if the stop event is set
        if self.stop_event.is_set():
            return True
        return False


class TextIteratorStreamerModified(TextIteratorStreamer):
    def stop(self):
        raise StopIteration()


class ModelLoader:
    def __init__(self, model_id, base_model, project, context_length=8192, model_type="", checkpoint="",
                 huggingface_url='', hf_repo_id=""):
        self.model_id = model_id
        self.base_model = base_model
        self.project = project
        self.context_length = int(context_length)
        self.model_type = model_type
        self.checkpoint = checkpoint
        self.huggingface_url = huggingface_url
        self.hf_repo_id = hf_repo_id
        self.model = None
        self.tokenizer = None
        self.streamer = None
        self.stop_event = None

    def load_model(self):
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.hf_repo_id,
                max_seq_length=self.context_length,
                dtype=None,
                load_in_4bit=True,
                use_auth_token=HFTokenManager().retrieve_token()
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to load foundational model: {e}")

    def stop_infer(self):
        if self.streamer:
            self.streamer.text_queue.put(self.streamer.stop_signal, timeout=self.streamer.timeout)
            self.stop_event.set()
            self.streamer = None
            return True
        return False

    def infer(self, prompt, temperature, max_new_tokens=8192):
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer must be loaded before inference.")
        FastLanguageModel.for_inference(self.model)
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
        self.stop_event = Event()
        stopping_criteria = CustomStoppingCriteria(self.stop_event)
        stopping_criteria_list = StoppingCriteriaList([stopping_criteria])
        self.streamer = TextIteratorStreamerModified(self.tokenizer)
        generation_kwargs = dict(inputs, streamer=self.streamer, max_new_tokens=max_new_tokens,
                                 stopping_criteria=stopping_criteria_list)
        if temperature:
            generation_kwargs.update({'temperature': float(temperature), 'do_sample': True})

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        return self.streamer

    def clean_model(self):
        if self.model is not None:
            print("cleaning current model..")
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            torch.cuda.empty_cache()

    def info(self):
        return json.dumps({
            'model_id': self.model_id,
            'base_model': self.base_model,
            'project': self.project,
            'context_length': self.context_length,
            'model_type': self.model_type,
            'checkpoint': self.checkpoint,
            'huggingface_url': self.huggingface_url,
            'hf_repo_id': self.hf_repo_id,
        })

    def __str__(self):
        return str(self.info())
