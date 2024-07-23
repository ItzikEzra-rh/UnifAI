from be_utils.gitlab import GitlabAPI
from be_utils.db.db import mongo, Collections, db

def get_directory_list(file_list_gitlab, file_list_db):
    """build a list of files from gitlab and add atrribute if each file is already in the database

    :param str[] file_list_gitlab: list of files from gitlab for product/version
    :param str[] file_list_db: list of files from database for product/version
    :param str version: number of version in gitlab/db (18.5/19.0)
    :return: list of file with state if it's in the db
    """

    database_set = {file_node["path"] + "/" +
                    file_node["name"] for file_node in file_list_db}
    list_of_files = [{'file': gitlab_file["path"], 'in_db': gitlab_file["path"] in database_set}
                     for gitlab_file in file_list_gitlab if
                     gitlab_file["name"].endswith(("jmx", "robot", "py")) and "__init__" not in str(gitlab_file)]

    return list_of_files

def list_of_files_from_gitlab(repo_url, repo_auth_key, repo_folder_path, branch):
    """creating a list of files form gitlab , for directory "product/param", and state file if he is in db

    :param str repo_url: representing the git repo url
    :param str repo_auth_key: authentication key for the dedicated git repo
    :param str repo_folder_path: valid folder to expand exist on the dedicated git repo
    :param str branch: valid branch to expand from under the dedicated git repo 
    :return: list of files from gitlab of product/version
    """
    gitlab = GitlabAPI(repo_url, repo_auth_key)
    file_list_gitlab = gitlab.list_files(repo_folder_path, branch)
    return get_directory_list(file_list_gitlab, [])

def insert_new_form(project_name, training_name, git_url, git_credential_key, git_folder_path, git_branch_name, base_model_name,
                    tests_code_framework, number_of_tests, expand_dataset_to, dataset_grading_upgrade):
    """inserting new form to the database

    :param str git_url: representing the git repo url
    :param str git_credential_key: authentication key for the dedicated git repo
    :param str git_folder_path: valid folder to expand exist on the dedicated git repo
    :param str git_branch_name: valid branch to expand from under the dedicated git repo 
    :return:
    """
    result = Collections.by_name('forms').insert_one({'projectName': project_name,
                                                      'trainingName': training_name,
                                                      'gitUrl': git_url,
                                                      'gitCredentialKey': git_credential_key})
    return result