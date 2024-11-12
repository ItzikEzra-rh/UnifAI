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


@backend_bp.route("/inference", methods=["GET"])
@from_query({
    "prompt": fields.Str(data_key="prompt", required=True),
    "temperature": fields.Str(data_key="temperature", required=False, default=None),
    "session_id": fields.Str(data_key="sessionId", required=False, default="N/A"),
})
def inference(prompt, temperature=None, session_id=""):
    return Response(llm_provider.inference(prompt, temperature, session_id=session_id), content_type='text/plain')


@backend_bp.route("/inference", methods=["POST"])
@from_body({
    "prompt": fields.Str(data_key="prompt", required=True),
    "temperature": fields.Str(data_key="temperature", required=False, default=None),
    "session_id": fields.Str(data_key="sessionId", required=False, default="N/A"),
    "context_length": fields.Str(data_key="contextLength", required=False, default="4096"),
})
def inference_post(prompt, temperature, session_id, context_length):
    return Response(llm_provider.inference(prompt,
                                           temperature,
                                           max_new_tokens=context_length,
                                           session_id=session_id),
                    content_type='text/plain')


@backend_bp.route("/stopInference", methods=["GET"])
@from_query({
    "session_id": fields.Str(data_key="sessionId", required=False, default="N/A"),
})
def stop_inference(session_id):
    return jsonify(llm_provider.stop_inference(session_id))


@backend_bp.route("/getModels", methods=["GET"])
def get_models():
    return jsonify(llm_provider.get_models())


@backend_bp.route("/saveToken", methods=["POST"])
@from_body({
    "token": fields.Str(data_key="token", required=True),
})
def save_token(token):
    return jsonify(llm_provider.save_hf_token(token))


@backend_bp.route("/getHfRepoFiles", methods=["GET"])
@from_query({
    "repo_id": fields.Str(data_key="repoId", required=True),
    "repo_type": fields.Str(data_key="repoType", required=True),
})
def get_hf_repo_files(repo_id, repo_type):
    return jsonify(llm_provider.get_hf_repo_files(repo_id, repo_type))


@backend_bp.route("/getLoadedModel", methods=["GET"])
def get_loaded_model():
    return jsonify(llm_provider.get_loaded_model())


@backend_bp.route("/unloadModel", methods=["GET"])
def unload_model():
    return jsonify(llm_provider.unload_model())


@backend_bp.route("/clearChatHistory", methods=["GET"])
@from_query({
    "session_id": fields.Str(data_key="sessionId", required=False, default="N/A"),
})
def clear_chat_history(session_id):
    return jsonify(llm_provider.clear_chat_history(session_id))


@backend_bp.route("/loadChatContext", methods=["POST"])
@from_body({
    "chat": fields.List(fields.Dict(), missing=[], required=False, data_key="chat"),
    "session_id": fields.String(data_key="sessionId", required=True),
})
def load_chat_context(chat, session_id):
    return jsonify(llm_provider.load_chat_context(chat, session_id))
