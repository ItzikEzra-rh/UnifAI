from llm.register import RegisterModel
from llm.model import ModelLoader
import llm.model as llm_model
from llm.hugging_face import HFTokenManager, HuggingFaceAPI


def register_trained_model(hf_url):
    return RegisterModel().register_model(hf_url)


def load_model(model_id):
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
    if llm_model.model_loader and llm_model.model_loader.model_id == model_id:
        return "model already loaded"
    elif llm_model.model_loader:
        llm_model.model_loader.clean_model()
    else:
        print(f"loading model with id {model_id}")

    llm_model.model_loader = ModelLoader(model_id, base_model, project, context_length,
                                         model_type, checkpoint, huggingface_url, hf_repo_id)
    return llm_model.model_loader.load_model()


def inference(prompt, temperature, max_new_tokens=8192):
    if not llm_model.model_loader:
        raise ValueError("No model loaded. Please load a model first.")
    return llm_model.model_loader.infer(prompt, temperature, max_new_tokens=max_new_tokens)


def stop_inference():
    global model_loader
    if llm_model.model_loader is not None:
        return llm_model.model_loader.stop_infer()
    return False


def get_models():
    return RegisterModel().get_models()


def save_hf_token(token):
    HFTokenManager().save_token(token)


def get_hf_repo_files(repo_id, repo_type):
    return HuggingFaceAPI().list_repo_files(repo_id, repo_type)
