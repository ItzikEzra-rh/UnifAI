from mas.config.app_config import AppConfig
from bootstrap.container import AppContainer
from inbound.flask.flask_app import create_app

config = AppConfig.get_instance()
container = AppContainer(config)
application = create_app(container, config=config)
