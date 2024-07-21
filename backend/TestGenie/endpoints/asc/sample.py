from flask import jsonify, Blueprint, make_response, Response, stream_with_context, after_this_request
import provider.asc.sample as sample
from be_utils.flask.api_args import from_body, from_query, Fields
from be_utils.utils import read_file_chunks
from webargs import fields
import gzip
import json
import os

asc_samples_bp = Blueprint("asc/sample", __name__)


@asc_samples_bp.route("/", methods=["GET"])
def sanity_check():
    return 'there is access to api asc sample'


@asc_samples_bp.route("/resources", methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def get_sample(sample_id):
    return sample.get_sample(sample_id)


@asc_samples_bp.route('/stages', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def get_sample_stages(sample_id):
    return sample.get_sample_stages(sample_id)


@asc_samples_bp.route('/start', methods=["POST"])
@from_body({
    "sample_template": fields.Dict(data_key="sampleTemplate", required=True),
    "sample_duration": fields.Str(data_key="sampleDuration", required=True),
    "sample_name": fields.Str(data_key="sampleName", required=True),
    "sample_filters": fields.List(fields.Dict(), data_key="sampleFilters", required=True)
})
def start_sample(sample_duration, sample_name, sample_template, sample_filters):
    return sample.start_sample(sample_name=sample_name,
                               sample_template=sample_template,
                               sample_duration=sample_duration,
                               sample_filters=sample_filters)


@asc_samples_bp.route('/data', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True),
    "sample_resources": fields.Str(data_key="sampleResources", required=True),
    "from_timestamp": fields.Str(data_key="fromTimestamp", required=False),
    "granularity": fields.Str(data_key="granularity", required=False),
    "direction": fields.Str(data_key="direction", required=False),
    "view": fields.Str(data_key="view", required=False),
    "is_live": fields.Bool(data_key="isLive", required=False),
})
def get_sample_data(sample_id, sample_resources, from_timestamp=None, granularity='1', direction='gte', view='vm',
                    is_live=False):
    sample_resources = json.loads(sample_resources)
    ret = sample.get_sample_data(sample_id, sample_resources, from_timestamp, granularity, direction, view, is_live)
    content = gzip.compress(json.dumps(ret).encode('utf8'), 9)
    response = make_response(content)
    response.headers['Content-length'] = len(content)
    response.headers['Content-Encoding'] = 'gzip'
    return response


@asc_samples_bp.route('/stop', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def stop_sample(sample_id):
    return jsonify(sample.stop_sample(sample_id))


@asc_samples_bp.route('/download', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def download_sample(sample_id):
    path_to_download = sample.get_sample_tar_path(sample_id)

    @after_this_request
    def after_request(response):
        sample.set_download_status(sample_id, status='INITIAL')
        return response

    if os.path.exists(path_to_download):
        return Response(
            stream_with_context(read_file_chunks(path_to_download)),
            headers={
                'Content-Disposition': f'attachment; filename={os.path.basename(path_to_download)}'
            }
        )
    else:
        raise FileNotFoundError


@asc_samples_bp.route('/dump', methods=["POST"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def dump_sample(sample_id):
    return jsonify(sample.dump_sample(sample_id))


@asc_samples_bp.route('/dumpStatus', methods=["GET"])
@from_query({
    "task_id": fields.Str(data_key="taskId", required=True)
})
def dump_sample_status(task_id):
    return jsonify(sample.dump_sample_status(task_id))


@asc_samples_bp.route('/downloadResourceMetricJson', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True),
    "parent_id": fields.Str(data_key="parentId", required=True),
    "vr_id": fields.Str(data_key="vrId", required=True),
    "filter_id": fields.Str(data_key="filterID", required=True),
    "filter_value": fields.Str(data_key="filterValue", required=True),
})
def dump_resource_metric(sample_id, parent_id, vr_id, filter_id, filter_value):
    path_to_download = sample.dump_resource_metric(sample_id, parent_id, vr_id, filter_id, filter_value)
    if os.path.exists(path_to_download):
        return Response(
            stream_with_context(read_file_chunks(path_to_download)),
            headers={
                'Content-Disposition': f'attachment; filename={os.path.basename(path_to_download)}'
            }
        )
    else:
        raise FileNotFoundError


@asc_samples_bp.route('/delete', methods=["DELETE"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def delete_sample(sample_id):
    return jsonify(sample.delete_sample(sample_id))


@asc_samples_bp.route('/alertFilter', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True),
    "filter_id": fields.Str(data_key="filterId", required=True)
})
def get_alert_by_filter(sample_id, filter_id):
    return jsonify(sample.get_alert_by_filter(sample_id, filter_id))


@asc_samples_bp.route('/resourcesByFilters', methods=["POST"])
@from_body({
    "filer_ids": fields.List(fields.Str, data_key="filterIds", required=True),
    "sample_id": fields.Str(data_key="sampleId", required=True)
})
def get_resources_by_filters(sample_id, filer_ids):
    return jsonify(sample.get_resources_by_filters(sample_id, filer_ids))


@asc_samples_bp.route('/resourceFilterData', methods=["POST"])
@from_body({
    "sample_id": fields.Str(data_key="sampleId", required=True),
    "filter_id": fields.Str(data_key="filterId", required=True),
    "resource": fields.Dict(data_key="resource", required=True)
})
def get_resource_filter_data(sample_id, filter_id, resource):
    return jsonify(sample.get_resource_filter_data(sample_id, filter_id, resource))


@asc_samples_bp.route('/statistics', methods=["GET"])
@from_query({
    "sample_id": fields.Str(data_key="sampleId", required=True),
})
def get_statistics(sample_id):
    return jsonify(sample.get_statistics(sample_id))
