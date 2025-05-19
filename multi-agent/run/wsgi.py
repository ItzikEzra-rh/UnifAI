from api.flask.flask_app import create_app
from config.app_config import AppConfig

config = AppConfig()
application = create_app(config=config)
