import logging
import os
import json
from flask import request, Blueprint
from flask import jsonify, Response
from webargs import fields
from bson import json_util
from backend.endpoints.schemas import MessageSchema
from helpers.apiargs import Fields, from_query, from_body
from be_utils.utils import json_response
from providers.backend import insert_new_prompt, get_saved_prompts, \
                              insert_prompt_comment, insert_prompt_is_complete, insert_prompt_rating
from providers.backend import insert_new_prompt, get_saved_prompts, \
                              insert_prompt_comment, insert_prompt_is_complete, insert_prompt_rating, delete_prompt, add_inference_counter_per_each_model, \
                              retrieve_inference_counter, retrieve_inference_counter_all

backend_bp = Blueprint("backend", __name__)

@backend_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to api backend'

@backend_bp.route("/savePrompt", methods=["POST"])
@from_body({
    "model_id":                    fields.Str(required=True, data_key="modelId"),
    "model_name":                  fields.Str(required=True, data_key="modelName"),
    "training_name":               fields.Str(required=True, data_key="trainingName"),
    "prompt_entire_text":          fields.Str(required=True, data_key="promptEntireText"),
    "prompt_user_latest_text":     fields.Str(required=True, data_key="promptUserLastQuestionText"),
    "prompt_llm_latest_text":      fields.Str(required=True, data_key="promptLLMLastAnswerText"),
    "prompt_name":                 fields.Str(required=True, data_key="promptName"),
})
def save_prompt(model_id, model_name, training_name, prompt_entire_text, prompt_user_latest_text, prompt_llm_latest_text, prompt_name):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_new_prompt(model_id, model_name, training_name, prompt_entire_text, prompt_user_latest_text, prompt_llm_latest_text, prompt_name)

        # Return success response with inserted id
        return jsonify({"status": "success", "inserted_id": str(result.inserted_id)}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@backend_bp.route("/retrievePrompt", methods=["GET"])
def retrieve_prompt():
    try:
        # Insert LLM prompt into MongoDB collection
        result = get_saved_prompts()

        # Return success response with inserted id
        return json_response({"result": result})

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@backend_bp.route("/savePromptComment", methods=["POST"])
@from_body({
    "model_id":        fields.Str(required=True, data_key="modelId"),
    "unique_id":       fields.Str(required=True, data_key="uniqueId"),
    "comment":         fields.Str(required=True, data_key="comment"),
})
def save_prompt_comment(model_id, unique_id, comment):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_prompt_comment(model_id, unique_id, comment)

        # Return success response
        return jsonify({"status": "success"}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@backend_bp.route("/markPromptAsComplete", methods=["POST"])
@from_body({
    "model_id":        fields.Str(required=True, data_key="modelId"),
    "unique_id":       fields.Str(required=True, data_key="uniqueId"),
    "completed":       fields.Bool(required=True, data_key="completed"),
})
def save_prompt_is_complete(model_id, unique_id, completed):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_prompt_is_complete(model_id, unique_id, completed)

        # Return success response
        return jsonify({"status": "success"}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@backend_bp.route("/ratePrompt", methods=["POST"])
@from_body({
    "model_id":           fields.Str(required=True, data_key="modelId"),
    "user_prompt":        fields.Str(required=True, data_key="prompt"),
    "response_prompt":    fields.Str(required=True, data_key="response"),
    "rating":             fields.Number(required=True, data_key="rating"),
    "rating_text":        fields.Str(missing='', data_key="ratingText"),
})
def save_prompt_rating(model_id, user_prompt, response_prompt, rating, rating_text):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_prompt_rating(model_id, user_prompt, response_prompt, rating, rating_text)

        # Return success response
        return jsonify({"status": "success"}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error rating new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@backend_bp.route("/deletePrompt", methods=["POST"])
@from_body({
    "unique_id":       fields.Str(required=True, data_key="uniqueId"),
})
def delete_prompt_from_db(unique_id):
    try:
        # Delete LLM pre-saved prompt from MongoDB collection
        result = delete_prompt(unique_id)

        # Return success response
        return jsonify({"status": "success"}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error deleting prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@backend_bp.route("/addInferenceCounter", methods=["POST"])
@from_body({
    "model_id":        fields.Str(required=True, data_key="modelId"),
    "model_name":      fields.Str(required=True, data_key="modelName"),
})
def add_inference_counter(model_id, model_name):
    try:
        # Increase the counter representing 'inference usage' per each model_id under MongoDB collection
        result = add_inference_counter_per_each_model(model_id, model_name)

        # Return success response
        return jsonify({"status": "success"}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error increase the counter of {model_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@backend_bp.route("/inferenceCounter", methods=["GET"])
@from_query({
    "model_id":        fields.Str(required=True, data_key="modelId"),
})
def retrieve_inference_counter_per_dedicated_model(model_id):
    try:
        # Retrieve the counter representing 'inference usage' per specific model_id under MongoDB collection
        result = retrieve_inference_counter(model_id)

        # Return success response
        return jsonify({"status": "success", "response": str(result)}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error retreive the counter of {model_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@backend_bp.route("/inferenceCounterAll", methods=["GET"])
def retrieve_inference_counter_per_all_models():
    try:
        # Retrieve the counter representing 'inference usage' per all models under MongoDB collection
        result = json.loads(json_util.dumps(retrieve_inference_counter_all()))

        # Return success response
        return jsonify({"status": "success", "response": result}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error retreive the counter of all models: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500