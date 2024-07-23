from be_utils.db.flaks_db import *


class RegisterModel:
    def __init__(self, collection_name='RegisteredModels'):
        self.db = db()
        self.collection = self.db.Collections.by_name(collection_name)

    def register_model(self, model_name, project, context_length, model_type):
        if model_type not in ['finetuned', 'checkpoint', 'foundational']:
            raise ValueError("Invalid model type. Must be 'finetuned', 'checkpoint', or 'foundational'.")

        if self.model_exists(model_name, project):
            return f"Model '{model_name}' for project '{project}' already exists."

        model_data = {
            "model_name": model_name,
            "project": project,
            "context_length": context_length,
            "model_type": model_type
        }
        result = self.collection.insert_one(model_data)
        return str(result.inserted_id)

    def update_model(self, model_id, **kwargs):
        model_id = as_object_id(model_id)
        update_data = {"$set": kwargs}
        result = self.collection.update_one({"_id": model_id}, update_data)
        return result.modified_count

    def get_model(self, model_id):
        model_id = as_object_id(model_id)
        model = self.collection.find_one({"_id": model_id})
        if model:
            model['_id'] = str(model['_id'])
        return model

    def get_models_by_project(self, project):
        models = self.collection.find({"project": project})
        models = [{**model, '_id': str(model['_id'])} for model in models]
        return models

    def model_exists(self, model_name, project):
        return self.collection.find_one({"model_name": model_name, "project": project}) is not None
