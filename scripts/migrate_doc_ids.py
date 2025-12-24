#!/usr/bin/env python3
"""
Migration Script: Convert doc_ids field from string array to object array.

This script migrates existing DocsDataflowRetriever resources from the old format:
    doc_ids: ["id1", "id2"]

To the new format with full objects that include display names:
    doc_ids: [{"id": "id1", "name": "Document 1"}, {"id": "id2", "name": "Document 2"}]

Usage:
    python migrate_doc_retrievers.py [--dry-run] [--mongodb-ip IP] [--mongodb-port PORT]

Options:
    --dry-run       Preview changes without modifying the database
    --mongodb-ip    MongoDB IP address (default: localhost)
    --mongodb-port  MongoDB port (default: 27017)
    --db-name       Database name (default: UnifAI)
"""

import argparse
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import pymongo
except ImportError:
    print("Error: pymongo is required. Install with: pip install pymongo")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


# Configuration
DATAFLOW_BASE_URL = "http://unifai-dataflow-server:13456"
RETRIEVER_TYPE = "docs_dataflow"
CATEGORY = "retrievers"


class DataflowClient:
    """Simple client to fetch document information."""
    
    def __init__(self, base_url: str = DATAFLOW_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def get_all_docs(self) -> Dict[str, str]:
        """Fetch all documents and return a mapping of id -> name."""
        docs_map = {}
        cursor = None
        
        print("  Fetching documents from Dataflow service...")
        
        with httpx.Client(timeout=self.timeout) as client:
            while True:
                params = {"limit": 100}
                if cursor:
                    params["cursor"] = cursor
                    
                try:
                    response = client.get(
                        f"{self.base_url}/api/docs/available.docs.get",
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    for doc in data.get("documents", []):
                        docs_map[doc["id"]] = doc["name"]
                    
                    if not data.get("hasMore", False):
                        break
                    cursor = data.get("nextCursor")
                    
                except Exception as e:
                    print(f"  Warning: Failed to fetch documents: {e}")
                    break
        
        print(f"  Found {len(docs_map)} documents")
        return docs_map


def convert_doc_ids(doc_ids: List[Any], docs_map: Dict[str, str]) -> List[Dict[str, str]]:
    """Convert doc_ids from old format to new format."""
    if not doc_ids:
        return []
    
    result = []
    for item in doc_ids:
        if isinstance(item, str):
            # Old format: just an ID string
            name = docs_map.get(item, item)  # Use ID as fallback if name not found
            result.append({"id": item, "name": name})
        elif isinstance(item, dict) and "id" in item:
            # Already in new format (or partial)
            if "name" not in item:
                item["name"] = docs_map.get(item["id"], item["id"])
            result.append(item)
        else:
            # Unknown format, skip
            print(f"    Warning: Unknown doc_id format: {item}")
    
    return result




def needs_migration(cfg_dict: Dict[str, Any]) -> bool:
    """Check if a resource's cfg_dict needs migration."""
    doc_ids = cfg_dict.get("doc_ids", [])
    
    # Check if doc_ids contains plain strings
    for item in (doc_ids or []):
        if isinstance(item, str):
            return True

    return False


def migrate_resources(
    mongodb_ip: str,
    mongodb_port: str,
    db_name: str,
    dry_run: bool = False,
    dataflow_url: str = DATAFLOW_BASE_URL
) -> Dict[str, int]:
    """
    Migrate all DocsDataflowRetriever resources to the new format.
    
    Returns:
        Dictionary with migration statistics
    """
    stats = {
        "total_checked": 0,
        "needs_migration": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Connect to MongoDB
    mongo_uri = f"mongodb://{mongodb_ip}:{mongodb_port}/"
    print(f"Connecting to MongoDB at {mongo_uri}...")
    
    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client[db_name]
        collection = db["resources"]
        
        # Verify connection
        client.admin.command('ping')
        print("  Connected successfully")
    except Exception as e:
        print(f"Error: Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    # Fetch document mappings from Dataflow
    print("\nFetching document information...")
    dataflow_client = DataflowClient(base_url=dataflow_url)
    
    try:
        docs_map = dataflow_client.get_all_docs()
    except Exception as e:
        print(f"Warning: Could not fetch from Dataflow service: {e}")
        print("  Will use IDs as names where lookup fails")
        docs_map = {}
    
    # Find all DocsDataflowRetriever resources
    print(f"\nSearching for {RETRIEVER_TYPE} resources...")
    query = {
        "category": CATEGORY,
        "type": RETRIEVER_TYPE
    }
    
    resources = list(collection.find(query))
    stats["total_checked"] = len(resources)
    print(f"  Found {len(resources)} resources")
    
    if not resources:
        print("\nNo resources found to migrate.")
        return stats
    
    # Process each resource
    print("\nProcessing resources...")
    print("-" * 60)
    
    for resource in resources:
        rid = resource.get("rid", resource.get("_id", "unknown"))
        name = resource.get("name", "unnamed")
        cfg_dict = resource.get("cfg_dict", {})
        
        print(f"\nResource: {name} (rid: {rid})")
        
        if not needs_migration(cfg_dict):
            print("  Status: Already migrated or no fields to migrate")
            stats["skipped"] += 1
            continue
        
        stats["needs_migration"] += 1
        
        # Get current values
        old_doc_ids = cfg_dict.get("doc_ids", [])
        
        print(f"  Current doc_ids: {json.dumps(old_doc_ids, default=str)}")
        
        # Convert to new format
        new_doc_ids = convert_doc_ids(old_doc_ids, docs_map)
        
        print(f"  New doc_ids: {json.dumps(new_doc_ids, default=str)}")
        
        if dry_run:
            print("  Status: Would migrate (dry-run mode)")
            continue
        
        # Update the resource
        try:
            new_cfg_dict = cfg_dict.copy()
            if old_doc_ids:
                new_cfg_dict["doc_ids"] = new_doc_ids
            
            result = collection.update_one(
                {"_id": resource["_id"]},
                {
                    "$set": {
                        "cfg_dict": new_cfg_dict,
                        "updated": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                print("  Status: Migrated successfully")
                stats["migrated"] += 1
            else:
                print("  Status: No changes made")
                stats["skipped"] += 1
                
        except Exception as e:
            print(f"  Status: Error - {e}")
            stats["errors"] += 1
    
    print("-" * 60)
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migrate DocsDataflowRetriever resources to new object format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying the database"
    )
    parser.add_argument(
        "--mongodb-ip",
        default="localhost",
        help="MongoDB IP address (default: localhost)"
    )
    parser.add_argument(
        "--mongodb-port",
        default="27017",
        help="MongoDB port (default: 27017)"
    )
    parser.add_argument(
        "--db-name",
        default="UnifAI",
        help="Database name (default: UnifAI)"
    )
    parser.add_argument(
        "--dataflow-url",
        default=DATAFLOW_BASE_URL,
        help=f"Dataflow service URL (default: {DATAFLOW_BASE_URL})"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DocsDataflowRetriever Migration Script")
    print("=" * 60)
    
    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")
    
    stats = migrate_resources(
        mongodb_ip=args.mongodb_ip,
        mongodb_port=args.mongodb_port,
        db_name=args.db_name,
        dry_run=args.dry_run,
        dataflow_url=args.dataflow_url
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"  Total resources checked: {stats['total_checked']}")
    print(f"  Needed migration:        {stats['needs_migration']}")
    print(f"  Successfully migrated:   {stats['migrated']}")
    print(f"  Skipped (already ok):    {stats['skipped']}")
    print(f"  Errors:                  {stats['errors']}")
    
    if args.dry_run and stats['needs_migration'] > 0:
        print("\n*** To apply changes, run without --dry-run ***")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


