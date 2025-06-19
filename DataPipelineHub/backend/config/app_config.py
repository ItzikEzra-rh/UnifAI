from global_utils.config.config import SharedConfig
from global_utils.utils.util import singleton

@singleton
class AppConfig(SharedConfig):
    rabbitmq_port: str = "5672"
    rabbitmq_ip: str = "0.0.0.0"
    broker_user_name: str = "guest"
    broker_password: str = "guest"
    mongodb_port: str = "27017"
    mongodb_ip: str = "0.0.0.0"
    hostname: str = "0.0.0.0"
    port: str = "13456"
