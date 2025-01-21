from endpoints.rag import rag_bp
from endpoints.chat_history import chat_history_bp
from endpoints.git import git_bp
from endpoints.forms import forms_bp
from endpoints.prompts import prompts_bp
from endpoints.inference import inference_bp


def register_all_endpoints(app):
    backend_blueprints = [
        {"bp": rag_bp, "parent": 'rag', "route": ''},
        {"bp": chat_history_bp, "parent": 'chatHistory', "route": ''},
        {"bp": git_bp, "parent": 'git', "route": ''},
        {"bp": forms_bp, "parent": 'forms', "route": ''},
        {"bp": prompts_bp, "parent": 'prompts', "route": ''},
        {"bp": inference_bp, "parent": 'inference', "route": ''},
    ]
    
    # register all other blueprints in the app
    for blueprint in backend_blueprints:
        app.register_blueprint(blueprint["bp"], url_prefix=f"/api/{blueprint['parent']}/{blueprint['route']}")
