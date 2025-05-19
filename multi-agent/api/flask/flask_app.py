import os
import sys

# Add the parent directory of 'multi-agent' (the root of the project) to the Python path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask, jsonify
from config.app_config import AppConfig
from core.app_container import AppContainer
from .endpoints import register_all_endpoints
from flask_cors import CORS
from global_utils.flask.request_rules import RequestRules


def create_app(config: AppConfig = None) -> Flask:
    """
    Application factory.

    1) Load config
    2) Build our DI container (singleton)
    3) Register Flask extensions
    4) Register API‐Blueprints (route groups)
    5) Register error handlers
    """
    config = config or AppConfig()
    app = Flask(__name__)
    CORS(app)

    container = AppContainer(config)
    app.container = container  # attach for routes to use
    register_all_endpoints(app)
    RequestRules(app)

    return app
