from config.manager import config


def get_mongo_url():
    path = config.get("mongodb.url")
    port = config.get("mongodb.port")
    return path.format(port=port)


def get_rabbitmq_url():
    path = config.get("rabbitmq.url")
    port = config.get("rabbitmq.port")
    return path.format(port=port)
