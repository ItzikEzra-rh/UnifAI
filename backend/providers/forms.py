from be_utils.db.db import mongo, Collections

@mongo
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
                                                      'gitCredentialKey': git_credential_key,
                                                      'gitFolderPath': git_folder_path,
                                                      'gitBranchName': git_branch_name,
                                                      'baseModelName': base_model_name,
                                                      'testsCodeFramework': tests_code_framework,
                                                      'numberOfTests': number_of_tests,
                                                      'expandDatasetTo': expand_dataset_to,
                                                      'datasetGradingUpgrade': dataset_grading_upgrade})
    return result

@mongo
def get_forms():
    """ getting all the existing forms from our forms collection
    
    :return: list of forms
    """
    result = Collections.by_name('forms').find()
    return result