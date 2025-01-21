import logging
from flask import Blueprint
from backend.endpoints.schemas import MessageSchema
from backend.providers.chat_history import delete_session_from_chat_history, get_chat_history, update_current_chat_history
from helpers.apiargs import from_query, from_body
from webargs import fields
from flask import jsonify

chat_history_bp = Blueprint("chatHistory", __name__)

@chat_history_bp.route("/getChats", methods=["GET"])
@from_query({
    "model_id":        fields.Str(required=True, data_key="modelId")
})
def get_chat_history_per_model(model_id):
    try:
        # Retrieve the chats saved in the DB for the current model
        result = get_chat_history(model_id)
        return jsonify({"status": "success", "response": result}), 200

    except Exception as e:
        logging.error(f"Error retreiving the chats for model: {model_id}")
        return jsonify({"status": "error", "message": str(e)}), 500

@chat_history_bp.route("/updateCurrentChat", methods=["POST"])
@from_body({
    "session_id":      fields.Str(required=True, data_key="sessionId"),
    "messages":        fields.List(fields.Nested(MessageSchema), required=True, data_key="messages"),
    "first_message":   fields.Str(required=True, data_key="firstMessage"),
    "model_id":        fields.Str(required=True, data_key="modelId"),
})
def update_current_chat(session_id, messages, first_message, model_id):
    try:
        result = update_current_chat_history(session_id, messages, first_message, model_id)
        return {"status": "success", "result": result}

    except Exception as e:
        logging.error(f"Error updating the chat for session: {session_id}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@chat_history_bp.route("/deleteChatSession", methods=["POST"])
@from_body({
    "session_id":       fields.Str(required=True, data_key="sessionId"),
})
def delete_chat_session(session_id):
    try:
        result = delete_session_from_chat_history(session_id)
        return {"status": "success", "result": result}

    except Exception as e:
        logging.error(f"Error deleting the chat session: {session_id}")
        return jsonify({"status": "error", "message": str(e)}), 500
    