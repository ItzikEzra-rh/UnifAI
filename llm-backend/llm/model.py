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

app = Flask(__name__)

# Global variable to hold the model and tokenizer
model_loader = None
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteriaList
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


class ModelLoaderFactory:
    @staticmethod
    def create_model_loader(model_id, model_type, model_name, context_length, project):
        if model_type == 'foundational':
            return FoundationalModelLoader(model_id=model_id, model_name=model_name, max_seq_length=context_length,
                                           project=project)
        elif model_type == 'checkpoint':
            return CheckpointModelLoader(model_id=model_id, model_name=model_name, max_seq_length=context_length,
                                         project=project)
        elif model_type == 'finetuned':
            return FineTunedModelLoader(model_id=model_id, model_name=model_name, max_seq_length=context_length,
                                        project=project)
        else:
            raise ValueError("Invalid model type")


class BaseModelLoader(ABC):
    def __init__(self, model_id, model_name=None, max_seq_length=8192, dtype=None, load_in_4bit=True, project=''):
        self.model_name = model_name
        self.max_seq_length = int(max_seq_length)
        self.dtype = dtype
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None
        self.model_id = model_id
        self.project = project
        self.streamer = None
        self.stop_event = None

    @abstractmethod
    def load_model(self):
        pass

    def stop_infer(self):
        if self.streamer:
            self.streamer.text_queue.put(self.streamer.stop_signal, timeout=self.streamer.timeout)
            self.stop_event.set()
            self.streamer = None
            return True
        return False

    def infer(self, prompt, max_new_tokens=8192):
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
            'model_name': self.model_name,
            'max_seq_length': self.max_seq_length,
            'dtype': self.dtype,
            'load_in_4bit': self.load_in_4bit,
            'model_id': self.model_id,
            'project': self.project
        })

    def __str__(self):
        return str(self.info())


class FoundationalModelLoader(BaseModelLoader):
    def load_model(self):
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_name,
                max_seq_length=self.max_seq_length,
                dtype=self.dtype,
                load_in_4bit=self.load_in_4bit,
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to load foundational model: {e}")


class CheckpointModelLoader(BaseModelLoader):
    def load_model(self):
        model_dir = Path('/home/instruct') / self.model_id
        if not os.path.exists(model_dir):
            raise ValueError(f"model directory {model_dir} does not exist")
        if not model_dir:
            raise ValueError(f"Checkpoint directory does not exist in {model_dir}")
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(str(model_dir))
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to load model from checkpoint: {e}")


class FineTunedModelLoader(BaseModelLoader):
    def load_model(self):
        model_dir = Path('/home/instruct') / self.model_id
        if not os.path.exists(model_dir):
            raise ValueError(f"model directory {model_dir} does not exist")

        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=str(model_dir),
                max_seq_length=self.max_seq_length,
                dtype=self.dtype,
                load_in_4bit=self.load_in_4bit,
            )
            FastLanguageModel.for_inference(self.model)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to load fine-tuned model: {e}")
