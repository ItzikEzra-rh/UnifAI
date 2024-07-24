from llm.register import RegisterModel
from llm.model import ModelLoaderFactory
import llm.model as llm_model


def register_trained_model(model_name, project, context_length, model_type):
    return RegisterModel().register_model(model_name, project, context_length, model_type)


def load_model(model_id):
    model_info = RegisterModel().get_model(model_id)
    if not model_info:
        raise ValueError(f"Model with ID {model_id} not found")

    model_type = model_info['model_type']
    model_name = model_info['model_name']
    project = model_info['project']
    context_length = model_info['context_length']

    # Clean the current model if one is already loaded
    if llm_model.model_loader:
        llm_model.model_loader.clean_model()

    llm_model.model_loader = ModelLoaderFactory.create_model_loader(model_id, model_type, model_name, context_length,
                                                                    project)
    return llm_model.model_loader.load_model()


def inference(prompt, max_new_tokens=8192):
    if not llm_model.model_loader:
        raise ValueError("No model loaded. Please load a model first.")
    return llm_model.model_loader.infer(prompt, max_new_tokens=max_new_tokens)


def stop_inference():
    global model_loader
    if llm_model.model_loader is not None:
        return llm_model.model_loader.stop_infer()
    return False
