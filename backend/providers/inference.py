from be_utils.db.db import mongo, Collections

@mongo
def add_inference_counter_per_each_model(model_id, model_name):
    """
    :param str  model_id:
    :param str  model_name:
    :return:
    """
    result = Collections.by_name('models').update_one({'modelId': model_id, 'modelName': model_name},
        {'$inc': {'inferenceCounter': 1}},
        upsert=True
    )
    return result

@mongo
def retrieve_inference_counter(model_id):
    """
    :param str  model_id:
    :return:
    """
    result = Collections.by_name('models').find_one({'modelId': model_id})
    return result

@mongo
def retrieve_inference_counter_all():
    """
    :return:
    """
    result = Collections.by_name('models').find()
    return list(result)

