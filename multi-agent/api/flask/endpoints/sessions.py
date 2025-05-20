from flask import Blueprint, jsonify, current_app, Response
from global_utils.helpers.apiargs import from_body, from_query
from webargs import fields
import json
from pydantic.json import pydantic_encoder

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/user.session.create", methods=["POST"])
@from_body({
    "blueprint_id": fields.Str(data_key="blueprintId", required=True),
    "user_id": fields.Str(data_key="userId", required=True),
    "metadata": fields.Dict(data_key="metadata", required=False, missing=lambda: {}, default=lambda: {}, ),
})
def create_user_session(blueprint_id, user_id, metadata):
    try:
        session_svc = current_app.container.session_service
        blueprint_svc = current_app.container.blueprint_service
        blueprint_spec = blueprint_svc.get_blueprint_spec(blueprint_id)
        session = session_svc.create(user_id=user_id,
                                     blueprint_spec=blueprint_spec,
                                     metadata=metadata)
        return jsonify(session.get_run_id()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route("/user.session.execute", methods=["POST"])
@from_body({
    "session_id": fields.Str(data_key="sessionId", required=True),
    "inputs": fields.Dict(data_key="inputs", required=True),
    "stream_mode": fields.List(fields.Str, data_key="streamMode", missing=lambda: ["custom"]),
    "stream": fields.Bool(data_key="stream", missing=False),
})
def execute_user_session(session_id, inputs, stream_mode, stream):
    """
    Execute (or stream) an existing session.
    - If `stream` is False (default), returns the full result as JSON.
    - If `stream` is True, returns an NDJSON stream of chunks.
    """
    svc = current_app.container.session_service

    if not stream:
        # synchronous run
        result = svc.execute(
            session_or_id=session_id,
            inputs=inputs,
            stream=False
        )
        return jsonify(result), 200

    # streaming run
    def generate():
        for chunk in svc.execute(
                session_or_id=session_id,
                inputs=inputs,
                stream=True,
                stream_mode=stream_mode
        ):
            # each chunk may include Pydantic models; use pydantic_encoder
            yield json.dumps(chunk, default=pydantic_encoder)

    return Response(
        generate(),
        mimetype="application/x-ndjson"
    )


@sessions_bp.route("/session.state.get", methods=["GET"])
@from_query({
    "session_id": fields.Str(data_key="sessionId", required=True),
})
def get_session_state(session_id):
    try:
        svc = current_app.container.session_service
        session = svc.get(run_id=session_id)
        return jsonify(session.get_state().model_dump(mode="json")), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route("/session.status.get", methods=["GET"])
@from_query({
    "session_id": fields.Str(data_key="sessionId", required=True),
})
def get_session_status(session_id):
    try:
        svc = current_app.container.session_service
        status = svc.get_status(run_id=session_id)
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
