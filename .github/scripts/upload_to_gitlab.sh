#!/bin/bash
set -euo pipefail
set -x

# Validate required environment variables
: "${BACKUP_REPO:?BACKUP_REPO environment variable is required}"
: "${BACKUP_REPO_NAME:?BACKUP_REPO_NAME environment variable is required}"
: "${MONGO_BACKUP_FILE:?MONGO_BACKUP_FILE environment variable is required}"
: "${QDRANT_SNAPSHOTS_DIR:?QDRANT_SNAPSHOTS_DIR environment variable is required}"

echo "Cloning gitlab repo"
git clone "$BACKUP_REPO"
echo "Cloned gitlab repo"

echo "Copying files to gitlab repo"
#mongo files
echo "Copying mongo backup file to gitlab repo"
cp "$MONGO_BACKUP_FILE" "$BACKUP_REPO_NAME/"

#qdrant files
SNAPSHOTS_DIRNAME=$(basename "$QDRANT_SNAPSHOTS_DIR")
if [ -d "$BACKUP_REPO_NAME/$SNAPSHOTS_DIRNAME" ]; then
    echo "Removing old snapshots directory"
    rm -rf "$BACKUP_REPO_NAME/$SNAPSHOTS_DIRNAME"
fi
cp -r "$QDRANT_SNAPSHOTS_DIR" "$BACKUP_REPO_NAME/"
echo "Copied files to gitlab repo"

echo "Committing changes to gitlab repo"
cd "$BACKUP_REPO_NAME"
git config user.email "sfiresht@redhat.com"
git config user.name "sfiresht"
git add .
git commit -m "uploading backup files to gitlab"
echo "Committed changes"
git push
echo "Pushed changes to gitlab repo"

echo "Cleaning up"
cd ..
rm -rf "$MONGO_BACKUP_FILE"
rm -rf "$QDRANT_SNAPSHOTS_DIR"
rm -rf "$BACKUP_REPO_NAME"
echo "Uploading files to gitlab repo completed"