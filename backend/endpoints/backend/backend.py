import logging
import os
from flask import request, Blueprint
from flask import jsonify, Response
from webargs import fields
from helpers.apiargs import Fields, from_query, from_body
from be_utils.utils import json_response
from providers.backend import list_of_files_from_gitlab, insert_new_form, insert_new_prompt, get_saved_prompts, insert_prompt_comment

backend_bp = Blueprint("backend", __name__)

@backend_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to api backend'

@backend_bp.route("/files", methods=["GET"])
@from_query({"repo_url":         fields.Str(missing='', data_key="gitUrl"),
             "repo_auth_key":    fields.Str(missing='', data_key="gitCredentialKey"),
             "repo_folder_path": fields.Str(missing='', data_key="gitFolderPath"),
             "branch":           fields.Str(missing='dev', data_key="gitBranchName")})
def get_test_list_from_gitlab(repo_url, repo_auth_key, repo_folder_path, branch):
    """calling gitlab api to get a list of files,

    check for each file if he is in the db

    :param str repo_url: representing the git repo url
    :param str repo_auth_key: authentication key for the dedicated git repo
    :param str repo_folder_path: valid folder to expand exist on the dedicated git repo
    :param str branch: valid branch to expand from under the dedicated git repo
    :return: list of files from gitlab, list of { 'file': filename, in_db: boolean }
    """
    list_of_files = list_of_files_from_gitlab(repo_url, repo_auth_key, repo_folder_path, branch)
    return json_response({"result": list_of_files})

@backend_bp.route("/forms", methods=["POST"])
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

@backend_bp.route("/savePrompt", methods=["POST"])
@from_body({
    "model_id":        fields.Str(required=True, data_key="modelId"),
    "training_name":   fields.Str(required=True, data_key="trainingName"),
    "prompt_text":     fields.Str(required=True, data_key="promptText"),
})
def save_prompt(model_id, training_name, prompt_text):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_new_prompt(model_id, training_name, prompt_text)

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
    "comment":         fields.Str(required=True, data_key="comment"),
})
def save_prompt_comment(model_id, comment):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_prompt_comment(model_id, comment)

        # Return success response
        return jsonify({"status": "success"}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500