#!/usr/bin/env python3
from qdrant_client import QdrantClient
import requests
import os

#constants to Qdrant cluster connection
QDRANT_MAIN_URL = "http://qdrant-route-tag-ai--pipeline.apps.stc-ai-e1-pp.imap.p1.openshiftapps.com"
# QDRANT_NODES = (
#     "http://qdrant-route-tag-ai--pipeline.apps.stc-ai-e1-pp.imap.p1.openshiftapps.com"
# )
QDRANT_API_KEY = ""
COLLECTION_NAME = "data_source_data"


# create the client to connect to the Qdrant cluster
# client = QdrantClient(QDRANT_MAIN_URL, api_key=QDRANT_API_KEY)

def create_snapshots(node_url: str, collection_name: str) -> str:
    '''
    Creates a snapshot of the collection from the given node URLs

    Args:
        node_url: node URL to create the snapshot from
        collection_name: name of the collection to create the snapshot from
    Returns:
        snapshot URL
    '''
    #snapshot_urls = []
    print(node_url)
    print("collection name: ", collection_name)
    client = QdrantClient(url=node_url, port=80, prefer_grpc=False, timeout=30.0)
    print('created client - create snapshots')
    #node_client = QdrantClient(node_url, api_key=QDRANT_API_KEY)
    snapshot_info = client.create_snapshot(collection_name=collection_name, wait=True)
    print('created snapshot')
    print(snapshot_info)
    snapshot_url = f"{node_url}/collections/{collection_name}/snapshots/{snapshot_info.name}"
    #snapshot_urls.append(snapshot_url)
    return snapshot_url

def download_all_snapshots(snapshot_urls: list[str]) -> None:
    '''
    Downloads the snapshots from the given URLs and saves them to the local filesystem
    beforehand, checks if the directory exists and creates it if it doesn't

    Args:
        snapshot_urls: list of snapshot URLs to download
    Returns:
        list of local snapshot paths
    '''
 
    os.makedirs("snapshots", exist_ok=True)

    local_snapshot_paths = []
    for snapshot_url in snapshot_urls:
        snapshot_name = os.path.basename(snapshot_url)
        local_snapshot_path = os.path.join("snapshots", snapshot_name)

        response = requests.get(
            snapshot_url, headers={"api-key": QDRANT_API_KEY}
        )
        with open(local_snapshot_path, "wb") as f:
            response.raise_for_status()
            f.write(response.content)

        local_snapshot_paths.append(local_snapshot_path)

def  get_collections(node_url: str) -> bool:
    '''
    Checks if the connection to the given node URL is successful
    '''
    try:
        client = QdrantClient(url=node_url, port=80, prefer_grpc=False, timeout=30.0)
        print('created client - get collections')
        collections = client.get_collections().collections
        print(collections)
        if collections:
            return collections
        # else:
        #     return False
    except Exception as e:
        print(f"Error checking connection to {node_url}: {e}")
        return False

def main():
    '''
    Main function to run the backup
    '''
    collections = get_collections(QDRANT_MAIN_URL)
    #print(collections)
    if not collections:
        print(f"Error getting collections from {QDRANT_MAIN_URL}")
        return
    snapshot_urls = []
    for collection in collections:
        print(collection)
        snapshot_url = create_snapshots(QDRANT_MAIN_URL, collection.name)
        snapshot_urls.append(snapshot_url)
    print(snapshot_urls)
    download_all_snapshots(snapshot_urls)

if __name__ == "__main__":
    main()