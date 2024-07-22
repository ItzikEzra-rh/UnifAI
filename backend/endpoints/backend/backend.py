import logging
import os
from flask import Blueprint
from flask import jsonify, Response
from webargs import fields
from helpers.apiargs import Fields, from_query, from_body
from be_utils.utils import json_response
from providers.backend import list_of_files_from_gitlab

backend_bp = Blueprint("backend", __name__)

@backend_bp.route("/", methods=["GET"])
def sanity_check():
    return 'There is access to api backend'

@backend_bp.route("/files", methods=["GET"])
@from_query({"repo_url":         fields.Str(missing='', data_key="gitUrl"),
             "repo_auth_key":    fields.Str(missing='', data_key="gitCredentialKey"),
             "repo_folder_path": fields.Str(missing='', data_key="gitFolderPath"),
             "branch":           fields.Str(missing='dev')})
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