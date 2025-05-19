from .backend import backend_blueprints

def register_all_endpoints(app):
    blueprints = backend_blueprints
    
    # register all other blueprints in the app
    for blueprint in blueprints:
        app.register_blueprint(blueprint["bp"], url_prefix=f"/api/{blueprint['parent']}/{blueprint['route']}")
