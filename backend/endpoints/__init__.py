from .backend import backend_bp
from rag.endpoints.backend.backend import rag_bp
from endpoints.chat_history import chat_history_bp
from endpoints.git import git_bp


def register_all_endpoints(app):
    backend_blueprints = [
        {"bp": backend_bp, "parent": 'backend', "route": ''},
        {"bp": rag_bp, "parent": 'rag', "route": ''},
        {"bp": chat_history_bp, "parent": 'chatHistory', "route": ''},
        {"bp": git_bp, "parent": 'git', "route": ''}
    ]
    
    # register all other blueprints in the app
    for blueprint in backend_blueprints:
        app.register_blueprint(blueprint["bp"], url_prefix=f"/api/{blueprint['parent']}/{blueprint['route']}")
