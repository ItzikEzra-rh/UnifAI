from typing import Dict, Any

from bson import ObjectId


class Instances:
    """
    Generic tracker for prompts progress, independent of the underlying storage.
    """


    def __init__(self, instances_handler, id):
        """
        :param statistics_handler: A MongoDataHandler instance for managing progress data.
        """
        self.instances_handler = instances_handler
        self.progress_id = id
        self._initialize_progress_data()

    def _initialize_progress_data(self) -> None:
        """
        Ensure progress data exists in the storage, initializing it if necessary.
        """
        if self.progress_id:
            existing_data = list(self.instances_handler.read_data(query={"_id": ObjectId(id)}))
            
            if not existing_data:
                inserted_id = self.statistics_handler.append_record(self.DEFAULT_VALUES)
                self.progress_id = inserted_id  
            else:
                self.progress_id = existing_data[0]["_id"]  

