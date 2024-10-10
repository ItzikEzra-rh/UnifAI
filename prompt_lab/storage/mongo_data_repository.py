# from storage.data_repository import DataRepository
# from utils.mongo_handler import Collections
#
#
# class MongoDataRepository(DataRepository):
#     def __init__(self, collection_name, progress_collection_name, processed_collection_name, project_id):
#         super().__init__(project_id)
#         self.collection = Collections.by_name(collection_name)
#         self.progress_collection = Collections.by_name(progress_collection_name)
#         self.processed_collection = Collections.by_name(processed_collection_name)
#
#     def load_data(self):
#         return list(self.collection.find({"project_id": self.project_id}))
#
#     def save_processed_data(self, data):
#         self.processed_collection.insert_many(data)
#
#     def save_progress(self, progress_data):
#         self.progress_collection.update_one(
#             {"project_id": self.project_id},
#             {"$set": {"current_index": progress_data}},
#             upsert=True
#         )
#
#     def load_progress(self):
#         progress_record = self.progress_collection.find_one({"project_id": self.project_id})
#         return progress_record.get("current_index", 0) if progress_record else 0
