from flask import Blueprint, jsonify, request
import provider.asc.asc as asc
from be_utils.flask.api_args import from_body, from_query
from webargs import fields
from asc.tasks.samples_info import SamplesInfo

asc_bp = Blueprint("asc", __name__)


@asc_bp.route("/", methods=["GET"])
def sanity_check():
    return 'there is access to api asc'


@asc_bp.route('/getSamples', methods=["GET"])
def get_samples():
    return jsonify(asc.get_samples())


@asc_bp.route('/restore', methods=["POST"])
def restore():
    request_file = request.files['file']
    return jsonify(asc.restore(request_file))


@asc_bp.route("/totalSize", methods=["GET"])
def get_total_size():
    return jsonify(SamplesInfo.get_samples_total_size())


@asc_bp.route('/filterKeys', methods=["GET"])
def get_filters():
    return jsonify(asc.get_filters())
