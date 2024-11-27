from endpoints import register_all_endpoints
from flask import Flask
from flask_cors import CORS
from llm_be_config.configParams import config_params
from be_utils.db.flaks_db import register_mongo
# from be_utils.utils import init_flask_logger
from endpoints.request_rules import RequestRules
import os

# Init FLASK
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*",
                                 "methods": ["GET", "POST", "OPTIONS"],
                                 "allow_headers": ["Content-Type", "Authorization"],
                                 "supports_credentials": True}})

# init_flask_logger('access.log')
# app.config['result_backend'] = config_params.MONGODB_URL
app.config['MONGO_URI'] = os.path.join(config_params.MONGODB_URL, config_params.MONGODB_BACKEND_COLLECTION)

app.db = register_mongo(app)

register_all_endpoints(app)

# Init before_request/after_request rules
RequestRules(app)

if __name__ == '__main__':
    hostname = config_params.get_param_by_env('hostname')
    port = config_params.get_param_by_env('backend_port')
    app.run(host=hostname, port=port, debug=True)
