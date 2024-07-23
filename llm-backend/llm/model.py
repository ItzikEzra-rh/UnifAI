import os
import subprocess
from flask import Flask, request, jsonify
from abc import ABC, abstractmethod
from unsloth import FastLanguageModel
from transformers import TextStreamer

app = Flask(__name__)

# Global variable to hold the model and tokenizer
model_loader = None


class BaseModelLoader(ABC):
    def __init__(self, model_name=None, checkpoint_dir=None, max_seq_length=8192, dtype=None, load_in_4bit=True):
        self.model_name = model_name
        self.checkpoint_dir = checkpoint_dir
        self.max_seq_length = max_seq_length
        self.dtype = dtype
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.tokenizer = None

    @abstractmethod
    def load_model(self):
        pass

    def infer(self, prompt, max_new_tokens=8192):
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model and tokenizer must be loaded before inference.")
        # EOS_TOKEN = self.tokenizer.eos_token
        FastLanguageModel.for_inference(self.model)
        inputs = self.tokenizer([prompt], return_tensors="pt").to("cuda")
        text_streamer = TextStreamer(self.tokenizer)
        output = self.model.generate(**inputs, streamer=text_streamer, max_new_tokens=max_new_tokens)
        return output

    def clean_model(self):
        if self.model is not None:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            subprocess.run(["sudo", "fuser", "-v", "/dev/nvidia*"], check=True)
            subprocess.run(["sudo", "pkill", "-9", "python"], check=True)


class FoundationalModelLoader(BaseModelLoader):
    def load_model(self):
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_name,
                max_seq_length=self.max_seq_length,
                dtype=self.dtype,
                load_in_4bit=self.load_in_4bit,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load foundational model: {e}")


class CheckpointModelLoader(BaseModelLoader):
    def load_model(self):
        if not os.path.exists(self.checkpoint_dir):
            raise ValueError(f"Checkpoint directory {self.checkpoint_dir} does not exist")
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(self.checkpoint_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to load model from checkpoint: {e}")


class FineTunedModelLoader(BaseModelLoader):
    def load_model(self):
        try:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_name,
                max_seq_length=self.max_seq_length,
                dtype=self.dtype,
                load_in_4bit=self.load_in_4bit,
            )
            FastLanguageModel.for_inference(self.model)
        except Exception as e:
            raise RuntimeError(f"Failed to load fine-tuned model: {e}")
