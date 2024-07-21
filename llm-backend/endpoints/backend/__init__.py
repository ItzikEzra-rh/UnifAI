from .backend import backend_bp

backend_blueprints = [
    {"bp": backend_bp, "parent": 'backend', "route": ''}
]