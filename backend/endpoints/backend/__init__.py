from .backend import backend_bp
from rag.endpoints.backend.backend import rag_bp

backend_blueprints = [
    {"bp": backend_bp, "parent": 'backend', "route": ''},
    {"bp": rag_bp, "parent": 'rag', "route": ''}
]