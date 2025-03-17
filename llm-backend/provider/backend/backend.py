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


def load_model(adapter_uid, vllm_port=8000):
    registry = AdapterRegistry()
    # Retrieve the base model document based on the provided adapter_uid.
    base_model_doc = registry.get_base_model_by_adapter(adapter_uid)
    model_uid = base_model_doc.get("uid")
    model_max_len = base_model_doc.get("context_length")
    adapters = registry.list_adapters(model_uid)
    # Load the vLLM model, passing along the current adapter UID.
    VLLMModelLoader.load(
        base_model_doc.get("base_model_name"),
        model_max_len,
        base_model_doc.get("quantized"),
        adapters,
        vllm_port,
        current_adapter_uid=adapter_uid)
    return True


def inference(adapter_uid: str,
              messages: list,
              temperature: float,
              max_new_tokens: int = 16000,
              session_id: str = "default"):
    """
    Perform inference using the loaded model.
    """
    if VLLMModelLoader.instance is None:
        raise ValueError("No model is currently loaded. Please load a model first.")
    registry = AdapterRegistry()
    # Retrieve the base model document based on the provided adapter_uid.
    adapter_name = registry.get_adapter_name_by_adapter_uid(adapter_uid)
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
    model = VLLMModelLoader.instance
    if model:
        return model.current_adapter_uid
    return None


def clear_chat_history(session_id):
    model = VLLMModelLoader.instance
    if model:
        model.clear_chat_history(session_id)
        return True
    return False


def load_chat_context(chat, session_id):
    model = VLLMModelLoader.instance
    if model:
        return model.load_chat_context(chat, session_id)
    return False
