from .blueprints import blueprints_bp
from .sessions import sessions_bp
from .catalog import catalog_bp
from .resources import resources_bp
from .graph import graph_bp
from .graph_validation import graph_validation_bp
from .element_actions import catalog_actions_bp


def register_all_endpoints(app):
    backend_blueprints = [
        {"bp": blueprints_bp, "parent": 'blueprints', "route": ''},
        {"bp": sessions_bp, "parent": 'sessions', "route": ''},
        {"bp": catalog_bp, "parent": 'catalog', "route": ''},
        {"bp": resources_bp, "parent": 'resources', "route": ''},
        {"bp": graph_bp, "parent": 'graph', "route": ''},
        {"bp": graph_validation_bp, "parent": 'graph', "route": 'validation'},
        {"bp": catalog_actions_bp, "parent": 'elements', "route": 'actions'},
    ]

    # register all other blueprints in the app
    for blueprint in backend_blueprints:
        app.register_blueprint(blueprint["bp"], url_prefix=f"/api/{blueprint['parent']}/{blueprint['route']}")