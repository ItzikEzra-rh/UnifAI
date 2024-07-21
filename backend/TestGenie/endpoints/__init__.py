from .lucid import lucid_blueprints
from .asc import asc_blueprints


def register_all_endpoints(app):
    blueprints = lucid_blueprints + asc_blueprints

    # register all other blueprints in the app
    for blueprint in blueprints:
        app.register_blueprint(blueprint["bp"], url_prefix=f"/api/{blueprint['parent']}/{blueprint['route']}")
