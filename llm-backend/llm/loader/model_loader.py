from abc import ABC, abstractmethod
import json
from threading import Event, Thread, Lock
from transformers import AutoTokenizer


# Abstract base class for ModelLoader
class AbstractModelLoader(ABC):
    load_lock = Lock()
    model_loader = None
    is_model_loading = False

    def __init__(self, model_id, base_model, project, context_length=8192, model_type="",
                 checkpoint="", huggingface_url='', hf_repo_id="", max_new_tokens=4096):
        self.model_id = model_id
        self.base_model = base_model
        self.project = project
        self.context_length = int(context_length)
        self.model_type = model_type
        self.checkpoint = checkpoint
        self.huggingface_url = huggingface_url
        self.hf_repo_id = hf_repo_id
        self.tokenizer = AutoTokenizer.from_pretrained(self.hf_repo_id)
        self.model = None
        self.streamer = None
        self.stop_event = None
        self.max_new_tokens = max_new_tokens

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def infer(self, prompt, temperature, max_new_tokens=8192):
        pass

    @abstractmethod
    def stop_infer(self):
        pass

    @abstractmethod
    def clean_model(self):
        pass

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

    def _format_prompt(self, system_message, input_text):
        """
        Formats the final prompt by combining the system message, context, and user input.

        Args:
            system_message (str): The system message, serving as an initial context for the prompt.
            context (str): The context generated for the prompt based on the element data.
            input_text (str): The main input text of the prompt generated from templates.

        Returns:
            str: The fully formatted prompt, ready for tokenization and processing.
        """
        return self.tokenizer.format_chat_prompt([
            {"role": "system", "content": system_message},
            # {"role": "context", "content": context},
            {"role": "user", "content": input_text}
        ])
