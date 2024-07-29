import logging
import os
from flask import Blueprint
from flask import jsonify, Response, stream_with_context
from webargs import fields
from be_utils.flask.api_args import from_body, from_query, abort
import provider.backend.backend as llm_provider

backend_bp = Blueprint("backend", __name__)


@backend_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to api backend'


@backend_bp.route("/registerTrainedModel", methods=["POST"])
@from_body({
    "model_name": fields.Str(data_key="modelName", required=True),
    "project": fields.Str(data_key="project", required=True),
    "context_length": fields.Int(data_key="contextLength", required=True),
    "model_type": fields.Str(data_key="type", required=True),
    "num_tests": fields.Str(data_key="numTests", required=True),
    "dataset_size": fields.Str(data_key="datasetSize", required=True),
    "checkpoint": fields.Str(data_key="checkpoint", required=False, default=""),
})
def register_trained_model(model_name, project, context_length, model_type, num_tests, dataset_size, checkpoint):
    return llm_provider.register_trained_model(model_name, project, context_length, model_type, num_tests, dataset_size,
                                               checkpoint)


@backend_bp.route("/loadModel", methods=["GET"])
@from_query({
    "model_id": fields.Str(data_key="modelId", required=True)
})
def load_model(model_id):
    return jsonify(llm_provider.load_model(model_id))


@backend_bp.route("/inference", methods=["GET"])
@from_query({
    "prompt": fields.Str(data_key="prompt", required=True),
})
def inference(prompt):
    return Response(llm_provider.inference(prompt), content_type='text/plain')


@backend_bp.route("/stopInference", methods=["GET"])
def stop_inference():
    return jsonify(llm_provider.stop_inference())


@backend_bp.route("/getModels", methods=["GET"])
def get_models():
    return jsonify(llm_provider.get_models())
