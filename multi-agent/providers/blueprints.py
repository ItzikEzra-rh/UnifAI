import pymongo
from services.service import BlueprintService
from blueprints.repository.mongo_blueprint_repository import MongoBlueprintRepository


def get_blueprints_list():
    """
    Get the list of blueprints from the MongoDB database.
    """
    try:
        # Initialize the MongoDB repository
        repo = MongoBlueprintRepository()
        # Initialize the Blueprint service with the repository
        service = BlueprintService(repo)
        # Retrieve the list of blueprints
        blueprints = service.list_dicts()
        return blueprints
    except pymongo.errors.PyMongoError as e:
        # Handle any MongoDB-related errors
        print(f"MongoDB error: {e}")
    except Exception as e:
        # Handle any other errors
        print(f"An error occurred: {e}")
