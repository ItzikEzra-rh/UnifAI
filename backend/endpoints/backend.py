import logging
import os
import json
from flask import request, Blueprint
from flask import jsonify, Response
from webargs import fields
from bson import json_util
from backend.endpoints.schemas import MessageSchema
from helpers.apiargs import from_query, from_body
from providers.backend import add_inference_counter_per_each_model, \
                              retrieve_inference_counter, retrieve_inference_counter_all

backend_bp = Blueprint("backend", __name__)

@backend_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to api backend'
    
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