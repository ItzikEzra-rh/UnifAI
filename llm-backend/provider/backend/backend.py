from llm.register import RegisterModel

def register_trained_model(app, model_name, project, context_length, model_type):
    RegisterModel(model_name, project, context_length, model_type)


def load_model(model_name, project, context_length):
    pass


def inference(prompt):
    pass


def stop_inference():
    pass
