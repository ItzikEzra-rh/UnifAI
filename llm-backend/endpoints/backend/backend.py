import logging
import os
from flask import Blueprint
from flask import jsonify, Response
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
    "context_length": fields.Int(data_key="context_length", required=True),
    "model_type": fields.Str(data_key="type", required=True),
})
def register_trained_model(model_name, project, context_length, model_type):
    llm_provider.register_trained_model(model_name, project, context_length, model_type)


@backend_bp.route("/registerTrainedModel", methods=["POST"])
@from_body({
    "model_name": fields.Str(data_key="modelName", required=True),
    "project": fields.Str(data_key="project", required=True),
    "context_length": fields.Int(data_key="context_length", required=True),
})
def load_model(model_name, project, context_length):
    llm_provider.load_model(model_name, project, context_length)


@backend_bp.route("/inference", methods=["GET"])
@from_body({
    "prompt": fields.Str(data_key="prompt", required=True),
})
def inference(prompt):
    pass


@backend_bp.route("/stopInference", methods=["GET"])
def stop_inference():
    llm_provider.stop_inference()
