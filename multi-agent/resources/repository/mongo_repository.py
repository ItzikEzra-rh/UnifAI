from typing import List
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
        self.col.create_index("nested_refs")
        self.col.create_index(
            [("user_id", 1), ("category", 1), ("type", 1), ("name", 1)],
            name="uq_user_cat_type_name",
            unique=True)

    def save(self, doc: ResourceDoc) -> str:
        """Insert a new resource document (create only)."""
        result = self.col.insert_one({"_id": doc.rid,
                                      **doc.model_dump(mode="json")})
        if not result.acknowledged:
            raise RuntimeError(f"Failed to insert document with rid: {doc.rid}")
        return doc.rid

    def update(self, doc: ResourceDoc) -> str:
        """Update an existing resource document."""
        result = self.col.replace_one(
            {"_id": doc.rid},
            doc.model_dump(mode="json")
        )
        if result.matched_count == 0:
            raise KeyError(f"No document found with rid: {doc.rid}")
        return doc.rid

    def get(self, rid: str) -> ResourceDoc:
        raw = self.col.find_one({"_id": rid})
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

    def meta(self, rid: str) -> tuple[str, str]:
        doc = self.col.find_one({"_id": rid}, {"category": 1, "type": 1})
        if not doc:
            raise KeyError(rid)
        return doc["category"], doc["type"]

    def count_nested(self, rid: str) -> int:
        return self.col.count_documents({"cfg_dict": {"$regex": rid}})

    def list_nested_usage(self, rid: str) -> List[str]:
        cur = self.col.find({"nested_refs": rid}, {"_id": 1})
        return [doc["_id"] for doc in cur]

    def exists(self, rid: str) -> bool:
        return self.col.count_documents({"_id": rid}, limit=1) == 1
