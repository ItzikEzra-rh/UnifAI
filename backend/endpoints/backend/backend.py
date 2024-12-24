import logging
import os
from flask import request, Blueprint
from flask_cors import cross_origin
from flask import jsonify, Response
from webargs import fields
from helpers.apiargs import Fields, from_query, from_body
from be_utils.utils import json_response
from providers.backend import get_test_content_from_gitlab, list_of_files_from_gitlab, insert_new_form, insert_new_prompt, get_forms, get_saved_prompts, \
                              insert_prompt_comment, insert_prompt_is_complete, insert_prompt_rating
from providers.backend import list_of_files_from_gitlab, insert_new_form, insert_new_prompt, get_forms, get_saved_prompts, \
                              insert_prompt_comment, insert_prompt_is_complete, insert_prompt_rating, delete_prompt, add_inference_counter_per_each_model, \
                              retrieve_inference_counter, retrieve_inference_counter_all

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

@backend_bp.route("/fileContent", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])

@from_query({"repo_url":         fields.Str(required=True, data_key="gitUrl"),
             "repo_auth_key":    fields.Str(required=True, data_key="gitCredentialKey"),
             "repo_folder_path": fields.Str(required=True, data_key="gitFolderPath"),
             "branch":           fields.Str(missing='dev', data_key="gitBranchName"),
             "test_path":        fields.Str(required=True, data_key="testPath")})
def get_test_details(repo_url, repo_auth_key, repo_folder_path, branch, test_path):
    """Fetch details for a specific test file from GitLab.

    :param str repo_url: Git repository URL
    :param str repo_auth_key: Authentication key for GitLab
    :param str repo_folder_path: Folder path in the Git repository
    :param str branch: Branch name
    :param str test_path: Path of the test file
    :return: Content of the test file
    """
    print(repo_url)
    test_content = get_test_content_from_gitlab(repo_url, repo_auth_key, branch, test_path)
    return json_response({"result": {"path": test_path, "content": test_content}})


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
    "model_id":                    fields.Str(required=True, data_key="modelId"),
    "training_name":               fields.Str(required=True, data_key="trainingName"),
    "prompt_entire_text":          fields.Str(required=True, data_key="promptEntireText"),
    "prompt_user_latest_text":     fields.Str(required=True, data_key="promptUserLastQuestionText"),
    "prompt_llm_latest_text":      fields.Str(required=True, data_key="promptLLMLastAnswerText"),
    "prompt_name":                 fields.Str(required=True, data_key="promptName"),
})
def save_prompt(model_id, training_name, prompt_entire_text, prompt_user_latest_text, prompt_llm_latest_text, prompt_name):
    try:
        # Insert LLM prompt into MongoDB collection
        result = insert_new_prompt(model_id, training_name, prompt_entire_text, prompt_user_latest_text, prompt_llm_latest_text, prompt_name)

        # Return success response with inserted id
        return jsonify({"status": "success", "inserted_id": str(result.inserted_id)}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error saving new prompt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@backend_bp.route("/retrieveForms", methods=["GET"])
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
        result = retrieve_inference_counter_all()

        # Return success response
        return jsonify({"status": "success", "response": str(result)}), 201

    except Exception as e:
        # Log the error and return error response
        logging.error(f"Error retreive the counter of all models: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500