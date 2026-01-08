#!/usr/bin/env python3
from qdrant_client import QdrantClient
import requests
import os
import sys
#constants to Qdrant cluster connection
QDRANT_MAIN_URL = os.getenv("QDRANT_URL")
QDRANT_PORT = 80
QDRANT_TIMEOUT = 30.0
QDRANT_API_KEY = ''

def create_snapshots(node_url: str, collection_name: str) -> str:
    '''
    Creates a snapshot of the collection from the given node URLs

    Args:
        node_url: node URL to create the snapshot from
        collection_name: name of the collection to create the snapshot from
    Returns:
        snapshot URL
    '''
    try:
        print(node_url)
        print("collection name: ", collection_name)
        client = QdrantClient(url=node_url, port=QDRANT_PORT, api_key=QDRANT_API_KEY, prefer_grpc=False, timeout=QDRANT_TIMEOUT)
        print('created client - create snapshots')
        #node_client = QdrantClient(node_url, api_key=QDRANT_API_KEY)
        snapshot_info = client.create_snapshot(collection_name=collection_name, wait=True)
        print('created snapshot')
        print(snapshot_info)
        snapshot_url = f"{node_url}/collections/{collection_name}/snapshots/{snapshot_info.name}"
        #snapshot_urls.append(snapshot_url)
        return snapshot_url
    except PermissionError as e:
      # Access denied to collection
      print(f"Permission denied for collection {collection_name}: {e}")
      sys.exit(1)
    except RuntimeError as e:
      # Snapshot creation failed
      print(f"Failed to create snapshot: {e}")
      sys.exit(1)

def download_all_snapshots(snapshot_urls: list[str]) -> None:
    '''
    Downloads the snapshots from the given URLs and saves them to the local filesystem
    beforehand, checks if the directory exists and creates it if it doesn't

    Args:
        snapshot_urls: list of snapshot URLs to download
    Returns:
        list of local snapshot paths
    '''
    try:
        os.makedirs("/tmp/snapshots", exist_ok=True)
        print('creating snapshots directory')
        for snapshot_url in snapshot_urls:
            print('downloading snapshot: ', snapshot_url)
            snapshot_name = os.path.basename(snapshot_url)
            local_snapshot_path = os.path.join("/tmp/snapshots", snapshot_name)

            response = requests.get(
                snapshot_url
            )
            with open(local_snapshot_path, "wb") as f:
                response.raise_for_status()
                f.write(response.content)
        print('snapshots downloaded')
        print('snapshots directory: ', os.listdir("snapshots"))
    except requests.exceptions.HTTPError as e:
        # Already raised by raise_for_status()
        print(f"HTTP error downloading snapshot: {e}")
        sys.exit(1)
    except PermissionError as e:
        # Can't write to directory
        print(f"Permission denied writing to disk: {e}")           
        sys.exit(1)
    except OSError as e:
        # File writing issues, disk full, etc.
        print(f"Failed to write snapshot to disk: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading snapshots: {e}")
        sys.exit(1)

def get_collections(node_url: str) -> list[object]:
    '''
    Checks if the connection to the given node URL is successful
    '''
    try:

        client = QdrantClient(url=node_url, port=QDRANT_PORT, api_key=QDRANT_API_KEY, prefer_grpc=False, timeout=QDRANT_TIMEOUT)
        print('created client - get collections')
        collections = client.get_collections().collections
        print(collections)
        if not collections:
            raise ValueError(f"No collections found at {node_url}")
        return collections
    except ValueError as e:
        # Invalid URL or parameters
        print(f"Invalid configuration for {node_url}: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"Error connecting to {node_url}: {e}")
        sys.exit(1)
    except TimeoutError as e:
        print(f"Timeout connecting to {node_url}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking connection to {node_url}: {e}")
        sys.exit(1)

def main():
    '''
    Main function to run the backup
    '''
    print(QDRANT_API_KEY)
    print(QDRANT_MAIN_URL)
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