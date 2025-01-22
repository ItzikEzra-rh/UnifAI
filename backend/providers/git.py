from backend.be_utils.gitlab import GitlabAPI

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

def get_test_content_from_gitlab(repo_url, repo_auth_key, branch, test_path):
    """Fetch test file content from GitLab.

    :param str repo_url: Git repository URL
    :param str repo_auth_key: Authentication key
    :param str branch: Branch name
    :param str test_path: Path of the test file
    :return: File content as a string
    """
    gitlab = GitlabAPI(repo_url, repo_auth_key)
    file_content = gitlab.get_file_content(test_path, branch)
    return file_content
