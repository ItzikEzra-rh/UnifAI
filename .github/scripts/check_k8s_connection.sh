#!/bin/bash
set -euo pipefail
set -x

echo "Setting up kubernetes connection"
kubectl config set-credentials "$CLUSTER" --token="$ACCESS_TOKEN"
kubectl config set-cluster "$CLUSTER" --server="$API_URL"
#here we combine the credentials and the cluster url to create a context, both has the same name.
kubectl config set-context "$CLUSTER" --user="$CLUSTER" --cluster="$CLUSTER"
kubectl config use-context "$CLUSTER"
echo "Checking pods and deployments"
kubectl get pods --namespace "$NAMESPACE"
kubectl get deployments --namespace "$NAMESPACE"