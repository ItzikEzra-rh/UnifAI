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
    "hf_url": fields.Str(data_key="hfUrl", required=True),
})
def register_trained_model(hf_url):
    return llm_provider.register_trained_model(hf_url)


@backend_bp.route("/loadModel", methods=["GET"])
@from_query({
    "model_id": fields.Str(data_key="modelId", required=True)
})
def load_model(model_id):
    return jsonify(llm_provider.load_model(model_id))


# @backend_bp.route("/inference", methods=["GET"])
# @from_query({
#     "prompt": fields.Str(data_key="prompt", required=True),
# })
# def inference(prompt):
#     return Response(llm_provider.inference(prompt), content_type='text/plain')


@backend_bp.route("/inference", methods=["POST"])
@from_body({
    "prompt": fields.Str(data_key="prompt", required=True),
    "context_length": fields.Str(data_key="contextLength", required=True),
})
def inference(prompt, context_length):
    return Response(llm_provider.inference(prompt, max_new_tokens=int(context_length)), content_type='text/plain')


@backend_bp.route("/stopInference", methods=["GET"])
def stop_inference():
    return jsonify(llm_provider.stop_inference())


@backend_bp.route("/getModels", methods=["GET"])
def get_models():
    return jsonify(llm_provider.get_models())


@backend_bp.route("/saveToken", methods=["POST"])
@from_body({
    "token": fields.Str(data_key="token", required=True),
})
def save_token(token):
    return jsonify(llm_provider.save_hf_token(token))
