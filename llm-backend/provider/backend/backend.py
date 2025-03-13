from llm.register import RegisterModel
from llm.register_adapter import AdapterRegistry
import llm.model as llm_model
from llm.hugging_face import HFTokenManager, HuggingFaceAPI
from llm.loader.model_loader import AbstractModelLoader

from llm.register_adapter import AdapterRegistry
from llm.loader.vllm_model_loader import VLLMModelLoader


def register_adapter(repo_id, checkpoint_step, epoch, checkpoint_repo_id=None):
    """
    Register an adapter using the AdapterRegistry.
    """
    registry = AdapterRegistry()
    return registry.register_adapter(repo_id, checkpoint_step, epoch, checkpoint_repo_id)


def get_registered_models():
    """
    Retrieve all registered base models.
    """
    registry = AdapterRegistry()
    return registry.get_all_models()


def load_model(model_uid, max_len=8000, vllm_port=8000):
    """
    Load (or reuse) a vLLM model. If the same base model is already loaded, it returns that instance.
    Otherwise, unloads the current model (if any) and loads the new one.
    """
    model = AdapterRegistry().get_base_model(model_uid)
    adapters = AdapterRegistry().list_adapters(model_uid)
    print(max_len)
    return VLLMModelLoader.load(model.get("base_model_name"), max_len, model.get("quantized"), adapters, vllm_port)


def inference(adapter_name: str,
              messages: list,
              temperature: float,
              max_new_tokens: int = 16000,
              session_id: str = "default"):
    """
    Perform inference using the loaded model.
    """
    if VLLMModelLoader.instance is None:
        raise ValueError("No model is currently loaded. Please load a model first.")
    return VLLMModelLoader.instance.infer(adapter_name, messages, temperature, max_new_tokens, session_id)


def stop_inference(session_id: str):
    """
    Stop the current inference session.
    """
    if VLLMModelLoader.instance is not None:
        return VLLMModelLoader.instance.stop_infer(session_id)
    return False


def unload_model():
    """
    Unload the current model.
    """
    if VLLMModelLoader.instance is not None:
        VLLMModelLoader.instance.unload()
        return True
    return False


def save_hf_token(token):
    HFTokenManager().save_token(token)


def get_hf_repo_files(repo_id, repo_type):
    return HuggingFaceAPI().list_repo_files(repo_id, repo_type)


def get_loaded_model():
    if AbstractModelLoader.model_loader:
        return AbstractModelLoader.model_loader.model_id
    return None


def clear_chat_history(session_id):
    if AbstractModelLoader.model_loader:
        AbstractModelLoader.model_loader.clear_chat_history(session_id)
        return True
    return False


def load_chat_context(chat, session_id):
    if AbstractModelLoader.model_loader:
        return AbstractModelLoader.model_loader.load_chat_context(chat, session_id)
    return False
