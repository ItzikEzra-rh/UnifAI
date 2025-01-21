import json
from flask import jsonify
from pymongo import ReturnDocument
from be_utils.gitlab import GitlabAPI
from be_utils.db.db import mongo, Collections, db
import uuid


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
def insert_new_prompt(model_id, model_name, training_name, prompt_entire_text, prompt_user_latest_text, prompt_llm_latest_text, prompt_name):
    """inserting new llm prompt response to the database

    :param str model_id:
    :param str model_name;
    :param str training_name:
    :param str prompt_entire_text: 
    :param str prompt_user_latest_text: 
    :param str prompt_llm_latest_text: 
    :param str prompt_name:
    :return:
    """
    # Generate a unique identifier
    unique_id = str(uuid.uuid4())

    result = Collections.by_name('prompts').insert_one({'modelId': model_id,
                                                        'modelName': model_name,
                                                        'uniqueId': unique_id,
                                                        'trainingName': training_name,
                                                        'promptText': prompt_entire_text,
                                                        'promptUserLatestText': prompt_user_latest_text,
                                                        'promptLLMLatestText': prompt_llm_latest_text,
                                                        'promptName': prompt_name,
                                                        'comment': ''})
    return result

@mongo
def get_forms():
    """ getting all the existing forms from our forms collection
    
    :return: list of forms
    """
    result = Collections.by_name('forms').find()
    return result

@mongo
def get_saved_prompts():
    """ getting all the saved prompts from our prompts collection
    
    :return: list of saved prompts
    """
    result = Collections.by_name('prompts').find()
    return result

@mongo
def insert_prompt_comment(model_id, unique_id, comment):
    """updating existing llm prompt comment in the database

    :param str model_id:
    :param str unique_id:
    :param str comment: 
    :return:
    """
    result = Collections.by_name('prompts').update_one({'modelId': model_id, 'uniqueId': unique_id}, {"$set": {"comment": comment}})
    return result

@mongo
def insert_prompt_is_complete(model_id, unique_id, completed):
    """updating existing llm prompt completed value in the database

    :param str  model_id:
    :param str  unique_id:
    :param bool completed: 
    :return:
    """
    result = Collections.by_name('prompts').update_one({'modelId': model_id, 'uniqueId': unique_id}, {"$set": {"completed": completed}})
    return result

@mongo
def delete_prompt(unique_id):
    """deleting existing llm prompt from the database

    :param str  unique_id:
    :return:
    """
    result = Collections.by_name('prompts').delete_one({'uniqueId': unique_id})
    return result


@mongo
def insert_prompt_rating(model_id, user_prompt, response_prompt, rating, rating_text):
    """Adding rating to Q/A in the database.

    :param str model_id: The ID of the model associated with the prompt.
    :param str user_prompt: The user's prompt to be rated.
    :param str response_prompt: The model's response to the user's prompt.
    :param int rating: The rating given by the user.
    :param str rating_text: The rating text explanation given by the user.
    :return: Result of the database operation.
    """
    query = {
        'modelId': model_id,
        'userPrompt': user_prompt,
        'responsePrompt': response_prompt
    }
    
    # If rating is 0, delete the existing rating if it exists
    if rating == 0:
        result = Collections.by_name('ratings').delete_one(query)
        return result
    
    # If a rating exists, update it; otherwise, insert a new one
    result = Collections.by_name('ratings').update_one(query, {"$set": {"rating": rating, 'ratingText': rating_text}}, upsert=True)
    return result

@mongo
def add_inference_counter_per_each_model(model_id, model_name):
    """
    :param str  model_id:
    :param str  model_name:
    :return:
    """
    result = Collections.by_name('models').update_one({'modelId': model_id, 'modelName': model_name},
        {'$inc': {'inferenceCounter': 1}},
        upsert=True
    )
    return result

@mongo
def retrieve_inference_counter(model_id):
    """
    :param str  model_id:
    :return:
    """
    result = Collections.by_name('models').find_one({'modelId': model_id})
    return result

@mongo
def retrieve_inference_counter_all():
    """
    :return:
    """
    result = Collections.by_name('models').find()
    return list(result)

