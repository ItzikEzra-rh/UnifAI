from endpoints.slack import slack_bp

def register_all_endpoints(app):
    backend_blueprints = [
        {"bp": slack_bp, "parent": 'slack', "route": ''},
    ]
    
    # register all other blueprints in the app
    for blueprint in backend_blueprints:
        app.register_blueprint(blueprint["bp"], url_prefix=f"/api/{blueprint['parent']}/{blueprint['route']}")
