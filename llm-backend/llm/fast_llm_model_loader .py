from transformers import TextIteratorStreamer, StoppingCriteriaList, StoppingCriteria
from threading import Thread, Event, Lock
import torch
from llm.hugging_face import HFTokenManager
from llm.model_loader import AbstractModelLoader
from unsloth import FastLanguageModel


class CustomStoppingCriteria(StoppingCriteria):
    def __init__(self, stop_event):
        self.stop_event = stop_event

    def __call__(self, input_ids, scores):
        if self.stop_event.is_set():
            return True
        return False


class TextIteratorStreamerModified(TextIteratorStreamer):
    def stop(self):
        raise StopIteration()


class FastLMModelLoader(AbstractModelLoader):
    def load_model(self):
        with FastLMModelLoader._load_lock:
            if self.model is not None:
                print("Model is already loaded.")
                return False
            try:  # Import here to avoid import conflicts
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

    def stop_infer(self):
        if self.streamer:
            self.streamer.text_queue.put(self.streamer.stop_signal, timeout=self.streamer.timeout)
            self.stop_event.set()
            self.streamer = None
            return True
        return False

    def clean_model(self):
        with FastLMModelLoader._load_lock:
            if self.model is not None:
                print("Cleaning current model..")
                del self.model
                del self.tokenizer
                self.model = None
                self.tokenizer = None
                torch.cuda.empty_cache()
            else:
                print("No model loaded to clean.")
