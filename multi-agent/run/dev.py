from mas.config.app_config import AppConfig
from bootstrap.container import AppContainer
from inbound.flask.flask_app import create_app

if __name__ == '__main__':
    config = AppConfig.get_instance()
    container = AppContainer(config)
    app = create_app(container, config=config)
    app.run(host=config.hostname, port=config.port, debug=True)
