from endpoints import register_all_endpoints
from flask import Flask
from be_utils.db.flaks_db import register_mongo
from endpoints.request_rules import RequestRules
import os

# Init FLASK
app = Flask(__name__)

app.db = register_mongo(app)


register_all_endpoints(app)

# Init before_request/after_request rules
RequestRules(app)

if __name__ == '__main__':
    hostname = "0.0.0.0"
    port = "9990"
    app.run(host=hostname, port=port, debug=True)
