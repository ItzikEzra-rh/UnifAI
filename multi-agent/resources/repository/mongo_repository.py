import json
import pymongo
from resources.models import ResourceDoc
from resources.repository.base import ResourceRepository


class MongoResourceRepository(ResourceRepository):
    def __init__(self, mongodb_port: str = "27017",
                 mongodb_ip: str = "localhost",
                 db_name="UnifAI",
                 coll_name="resources"):
        mongo_uri = f"mongodb://{mongodb_ip}:{mongodb_port}/"
        client = pymongo.MongoClient(mongo_uri)
        self.col = client[db_name][coll_name]

    def save(self, doc: ResourceDoc) -> str:
        self.col.replace_one({"_id": doc.uuid},
                             json.loads(doc.model_dump_json()),
                             upsert=True)
        return doc.uuid

    def get(self, rid: str) -> ResourceDoc:
        raw = self.col.find_one({"_id": rid})
        print(raw)
        if not raw:
            raise KeyError(rid)
        return ResourceDoc(**raw)

    def delete(self, rid: str) -> None:
        self.col.delete_one({"_id": rid})

    def find_by_name(self, user_id: str, category: str, type: str, name: str):
        raw = self.col.find_one({"user_id": user_id, "category": category, "type": type, "name": name})
        return ResourceDoc(**raw) if raw else None

    def count(self, user_id, filter):
        return self.col.count_documents({"user_id": user_id, **filter})
