from celery_app.tasks import start_sample_task, sample_dump_task
from asc.sample.sample import Sample
from be_utils.utils import retry
import os


def start_sample(sample_name, sample_duration, sample_template, sample_filters):
    task = start_sample_task.delay(sample_name=sample_name,
                                   sample_template=sample_template,
                                   sample_duration=sample_duration,
                                   sample_filters=sample_filters)
    res = {'task_id': task.id,
           'stages': get_sample_stages(sample_id=task.id)}
    return res


def stop_sample(sample_id):
    return Sample.init_from_sample_id(sample_id=sample_id).stop()


@retry(tries=2)
def get_sample_stages(sample_id):
    """
    Function that gets the stages of a given sample
    we call this function when we expect an object of the sample to be in the db, but if the sample object in the
    process of being added to the db and still not being added, we want to give the sample object some time/chance
    to be inserted to the db so we use a retry function to try few times to get the stages
    :param sample_id:
    :return:
        on :success - json
            "agentsValidation": "DONE",
            "ascValidation": "IN PROGRESS",
            "dataBaseInsertion": "PENDING",
            "prepareResources": "DONE",
            "spawnAgents": "DONE"
        on :failure - boolean
            False
    """
    return Sample.init_from_sample_id(sample_id=sample_id).get_stages()


def get_sample(sample_id):
    return Sample.init_from_sample_id(sample_id=sample_id).get_sample()


def get_sample_data(sample_id, sample_resources, from_timestamp, granularity, direction, view, is_live):
    return Sample.init_from_sample_id(sample_id=sample_id).get_data(sample_resources,
                                                                    from_timestamp,
                                                                    int(granularity),
                                                                    direction,
                                                                    view,
                                                                    is_live)


def delete_sample(sample_id):
    return Sample.init_from_sample_id(sample_id=sample_id).delete()


def dump_sample(sample_id):
    task = sample_dump_task.delay(sample_id)
    return task.id


def dump_sample_status(task_id):
    return sample_dump_task.AsyncResult(task_id).state


def get_sample_tar_path(sample_id):
    path = Sample.init_from_sample_id(sample_id=sample_id).get_tar_path()
    if os.path.exists(path):
        return path


def dump_resource_metric(sample_id, parent_id, vr_id, filter_id, filter_value):
    return Sample.init_from_sample_id(sample_id=sample_id).dump_resource_metric(parent_id, vr_id, filter_id,
                                                                                filter_value)


def get_sample_json_tar_path(sample_id):
    statistic_json_tar_path = Sample.init_from_sample_id(sample_id=sample_id).get_json_path(tar=True)
    if os.path.exists(statistic_json_tar_path):
        return statistic_json_tar_path
    return None


def set_download_status(sample_id, status):
    sample = Sample.init_from_sample_id(sample_id=sample_id)
    sample.set(download_status=status)


def get_alert_by_filter(sample_id, filter_id):
    return Sample.init_from_sample_id(sample_id=sample_id).get_alert_by_filter(filter_id)


def get_resources_by_filters(sample_id, filter_ids):
    return Sample.init_from_sample_id(sample_id=sample_id).get_resources_by_filters(filter_ids)


def get_resource_filter_data(sample_id, filter_id, resource):
    return Sample.init_from_sample_id(sample_id=sample_id).get_resource_filter_data(filter_id, resource)


def get_statistics(sample_id):
    return Sample.init_from_sample_id(sample_id=sample_id).get_statistics()
