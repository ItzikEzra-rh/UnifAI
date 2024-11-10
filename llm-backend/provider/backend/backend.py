from llm.register import RegisterModel
import llm.model as llm_model
from llm.hugging_face import HFTokenManager, HuggingFaceAPI
from llm.loader.vllm_model_loader import VLLMModelLoader
from llm.loader.model_loader import AbstractModelLoader


def register_trained_model(hf_url):
    return RegisterModel().register_model(hf_url)


def load_model(model_id):
    if AbstractModelLoader.model_loader:
        return "There is already a loaded model, please unload the model first."
    if AbstractModelLoader.is_model_loading:
        return "There is a loading model process happening now."

    with AbstractModelLoader.load_lock:
        AbstractModelLoader.is_model_loading = True
        model_info = RegisterModel().get_model(model_id)
        if not model_info:
            raise ValueError(f"Model with ID {model_id} not found")

        base_model = model_info.get('base_model', 'Unknown')
        project = model_info.get('project', 'Unknown')
        context_length = model_info.get('context_length', 0)
        model_type = model_info.get('model_type', 'Unknown')
        checkpoint = model_info.get('checkpoint', "")
        huggingface_url = model_info.get('huggingface_url', 'Unknown')
        hf_repo_id = model_info.get('hf_repo_id', "")

        # Clean the current model if one is already loaded
        # if AbstractModelLoader.model_loader and AbstractModelLoader.model_loader.model_id == model_id:
        #     return "model already loaded"
        # elif AbstractModelLoader.model_loader:
        # if AbstractModelLoader.model_loader:
        #     AbstractModelLoader.model_loader.clean_model()
        # else:
        #     print(f"loading model with id {model_id}")

        model = VLLMModelLoader(model_id, base_model, project, context_length,
                                model_type, checkpoint, huggingface_url, hf_repo_id)
        res = model.load_model()
        AbstractModelLoader.model_loader = model
        AbstractModelLoader.is_model_loading = False
        return res


def inference(prompt, temperature, max_new_tokens=4096, session_id=""):
    model = AbstractModelLoader.model_loader
    if not model:
        raise ValueError("No model loaded. Please load a model first.")
    return model.infer(prompt, temperature, max_new_tokens=max_new_tokens, session_id=session_id)


def stop_inference(session_id):
    if AbstractModelLoader.model_loader is not None:
        return AbstractModelLoader.model_loader.stop_infer(session_id)
    return False


def get_models():
    return RegisterModel().get_models()


def save_hf_token(token):
    HFTokenManager().save_token(token)


def get_hf_repo_files(repo_id, repo_type):
    return HuggingFaceAPI().list_repo_files(repo_id, repo_type)


def get_loaded_model():
    if AbstractModelLoader.model_loader:
        return AbstractModelLoader.model_loader.model_id
    return None


def unload_model():
    if AbstractModelLoader.is_model_loading:
        return "There is a loading model process happening now."

    with AbstractModelLoader.load_lock:
        if AbstractModelLoader.model_loader:
            AbstractModelLoader.model_loader.clean_model()
            del AbstractModelLoader.model_loader
            AbstractModelLoader.model_loader = None
            return True
        return False


def clear_chat_history(session_id):
    if AbstractModelLoader.model_loader:
        AbstractModelLoader.model_loader.clear_chat_history(session_id)
        return True
    return False


def load_chat_context(chat, session_id):
    if AbstractModelLoader.model_loader:
        return AbstractModelLoader.model_loader.load_chat_context(chat, session_id)
    return False
