import logging
from flask import Blueprint
from backend.be_utils.utils import json_response
from backend.providers.forms import get_forms, insert_new_form
from helpers.apiargs import from_body
from webargs import fields
from flask import jsonify

forms_bp = Blueprint("forms", __name__)

@forms_bp.route("/insert", methods=["POST"])
@from_body({
    "project_name":            fields.Str(required=True, data_key="projectName"),
    "training_name":           fields.Str(required=True, data_key="trainingName"),
    "git_url":                 fields.Str(required=True, data_key="gitUrl"),
    "git_credential_key":      fields.Str(required=True, data_key="gitCredentialKey"),
    "git_folder_path":         fields.Str(missing='', data_key="gitFolderPath"),
    "git_branch_name":         fields.Str(required=True, data_key="gitBranchName"),
    "base_model_name":         fields.Str(required=True, data_key="baseModelName"),
    "tests_code_framework":    fields.Str(required=True, data_key="testsCodeFramework"),
    "number_of_tests":         fields.Int(missing=None, data_key="numberOfTests"),
    "expand_dataset_to":       fields.Str(missing=None, data_key="expandDatasetTo"),
    "dataset_grading_upgrade": fields.Bool(missing=False, data_key="datasetGradingUpgrade"),
})
def insert_form(project_name, training_name, git_url, git_credential_key, git_folder_path, git_branch_name, base_model_name,
                tests_code_framework, number_of_tests, expand_dataset_to, dataset_grading_upgrade):
    try:
        # Insert form data into MongoDB collection
        result = insert_new_form(project_name, training_name, git_url, git_credential_key, git_folder_path, git_branch_name, base_model_name,
                                 tests_code_framework, number_of_tests, expand_dataset_to, dataset_grading_upgrade)

        # Return success response with inserted id
        return jsonify({"status": "success", "inserted_id": str(result.inserted_id)}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving form data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@forms_bp.route("retrieve", methods=["GET"])
def retrieve_forms():
    try:
        # Insert LLM prompt into MongoDB collection
        result = get_forms()

        # Return success response with inserted id
        return json_response({"result": result})

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error retrieving existing forms: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500