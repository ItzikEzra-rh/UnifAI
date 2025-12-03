from typing import List
import pymongo
from resources.models import ResourceDoc, ResourceQuery
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
        # Add index for better query performance
        self.col.create_index([("user_id", 1), ("created", -1)])

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

    def find_resources(self, query: ResourceQuery) -> List[ResourceDoc]:
        """Find resources based on query criteria with pagination."""
        filter_dict = {"user_id": query.user_id}
        
        if query.category:
            filter_dict["category"] = query.category.value  # Use enum value
        if query.type:
            filter_dict["type"] = query.type
            
        # Build cursor with filtering
        cursor = self.col.find(filter_dict)
        
        # Apply sorting
        sort_direction = pymongo.DESCENDING if query.sort_order == "desc" else pymongo.ASCENDING
        cursor = cursor.sort(query.sort_by, sort_direction)
        
        # Apply pagination
        if query.offset:
            cursor = cursor.skip(query.offset)
        if query.limit:
            cursor = cursor.limit(query.limit)
            
        return [ResourceDoc(**doc) for doc in cursor]

    def count_resources(self, query: ResourceQuery) -> int:
        """Count resources matching query criteria."""
        filter_dict = {"user_id": query.user_id}
        
        if query.category:
            filter_dict["category"] = query.category.value
        if query.type:
            filter_dict["type"] = query.type
            
        return self.col.count_documents(filter_dict)

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

    def aggregate_by_category(self, user_id: str) -> List[dict]:
        """
        Aggregate resources by category and type.
        """
        # Get only category and type fields (minimal data transfer)
        cursor = self.col.find(
            {"user_id": user_id},
            {"category": 1, "type": 1, "_id": 0}
        )
        
        # Group by category and type in Python
        results_dict = {}
        for doc in cursor:
            category = doc.get("category")
            type_name = doc.get("type")
            
            if not category:
                continue
            
            if category not in results_dict:
                results_dict[category] = {"count": 0, "types": {}}
            
            results_dict[category]["count"] += 1
            if type_name:
                results_dict[category]["types"][type_name] = \
                    results_dict[category]["types"].get(type_name, 0) + 1
        
        # Convert to list format
        return [
            {"category": cat, "count": data["count"], "types": data["types"]}
            for cat, data in results_dict.items()
        ]