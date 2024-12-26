"""
mongo_data_handler.py

A DataHandler implementation that stores and retrieves data from MongoDB.
"""

from typing import Any, Dict, Iterator, List
from pymongo import MongoClient
from .data_handler import DataHandler


class MongoDataHandler(DataHandler):
    """
    A DataHandler that uses a MongoDB collection to store records.
    Each call to append_record inserts a document.
    read_data iterates over all documents in the collection.
    """

    def __init__(
            self,
            uri: str,
            db_name: str,
            collection_name: str,
            query: Dict[str, Any] = None
    ):
        """
        :param uri: MongoDB connection URI (e.g., "mongodb://localhost:27017/")
        :param db_name: Name of the MongoDB database.
        :param collection_name: Name of the collection to store/retrieve records.
        :param query: (Optional) A default MongoDB filter to apply when reading data.
        """
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.query = query or {}
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def read_data(self) -> Iterator[Dict[str, Any]]:
        """
        Stream data from the MongoDB collection as dictionaries.
        """
        cursor = self.collection.find(self.query)
        for doc in cursor:
            # Convert _id to str for convenience, or remove it.
            doc["_id"] = str(doc["_id"])
            yield doc

    def append_record(self, record: Dict[str, Any]) -> None:
        """
        Insert a single record (document) into the collection.
        """
        self.collection.insert_one(record)

    def append_records(self, records: List[Dict[str, Any]]) -> None:
        """
        Insert multiple records at once for efficiency.
        """
        if records:
            self.collection.insert_many(records)

    def close(self) -> None:
        """
        Close the MongoDB client connection.
        """
        self.client.close()
