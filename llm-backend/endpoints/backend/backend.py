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


@backend_bp.route("/registerAdapter", methods=["POST"])
@from_body({
    "repo_id": fields.Str(data_key="repoId", required=True),
    "epoch": fields.Integer(data_key="epoch", required=True),
    "checkpoint_step": fields.Integer(data_key="checkpointStep", required=True),
})
def register_adapter(repo_id, checkpoint_step, epoch):
    return llm_provider.register_adapter(repo_id, checkpoint_step, epoch)


@backend_bp.route("/loadModel", methods=["GET"])
@from_query({
    "model_id": fields.Str(data_key="modelId", required=True),
    # "context_length": fields.Str(data_key="contextLength", missing=None)
})
def load_model(model_id):
    return jsonify(llm_provider.load_model(model_id))


@backend_bp.route("/inference", methods=["GET"])
@from_query({
    "adapter_name": fields.Str(data_key="adapterName", required=True),
    "prompt": fields.Str(data_key="prompt", required=True),
    "temperature": fields.Str(data_key="temperature", required=False, default=None),
    "session_id": fields.Str(data_key="sessionId", required=False, default="N/A"),
})
def inference(adapter_name, prompt, temperature=None, session_id=""):
    return Response(llm_provider.inference(adapter_name,
                                           prompt,
                                           temperature,
                                           session_id=session_id),
                    content_type='text/plain')


@backend_bp.route("/inference", methods=["POST"])
@from_body({
    "adapter_name": fields.Str(data_key="adapterName", required=False, missing=None),
    "messages": fields.List(fields.Dict(), missing=[], required=False, data_key="messages"),
    "temperature": fields.Str(data_key="temperature", required=False, missing=None),
    "session_id": fields.Str(data_key="sessionId", required=False, missing="N/A"),
    "max_gen_len": fields.Str(data_key="maxGenLen", required=False, missing="12000"),
})
def inference_post(adapter_name, messages, temperature, session_id, max_gen_len):
    return Response(llm_provider.inference(adapter_name,
                                           messages,
                                           temperature,
                                           max_new_tokens=int(max_gen_len),
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
    return jsonify(llm_provider.get_registered_models())


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
