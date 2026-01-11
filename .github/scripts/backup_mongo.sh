#!/bin/bash
set -euo pipefail
set -x

# Validate required environment variables
: "${NAMESPACE:?NAMESPACE environment variable is required}"
: "${MONGO_POD:?MONGO_POD environment variable is required}"
: "${MONGO_URI:?MONGO_URI environment variable is required}"

echo "Removing old backup if they exist"
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- rm -rf /tmp/backup
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- rm -rf /tmp/backup.tar.gz
echo "Temporary files removed"

echo "Testing mongodump availability and MongoDB connection"
if ! kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- which mongodump; then
    echo "ERROR: mongodump not found in PATH"
    exit 1
fi

if ! kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- mongosh --eval "db.version()" "${MONGO_URI}"; then
    echo "ERROR: MongoDB connection test failed"
    exit 1
fi

echo "Running mongodump with URI: ${MONGO_URI}"
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- mongodump --uri="${MONGO_URI}" --out="/tmp/backup" 2>&1 || (echo "mongodump failed with exit code $?" && exit 1)
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- ls -la /tmp/backup 2>/dev/null
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- tar -czf /tmp/backup.tar.gz /tmp/backup
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- ls -la /tmp/backup.tar.gz

echo "Copying backup file to local machine"
kubectl cp --namespace "$NAMESPACE" --retries=10 "$MONGO_POD":/tmp/backup.tar.gz /tmp/backup.tar.gz
ls -la /tmp/backup.tar.gz
echo "Backup file copied to local machine"

echo "Removing temporary files"
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- rm -rf /tmp/backup
kubectl exec --namespace "$NAMESPACE" "$MONGO_POD" -- rm -rf /tmp/backup.tar.gz
echo "Temporary files removed"

echo "Backup completed"