#!/bin/bash

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "Starting postsync hook for dataflow"

# Function to wait for service port
wait_for_port() {
    local svc=$1
    local max_attempts=60
    local sleep_time=10
    
    log_info "Waiting for service '$svc' port..."
    
    for i in $(seq 1 $max_attempts); do
        port=$(kubectl get svc "$svc" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
        if [[ -n "$port" ]]; then
            log_info "Service '$svc' port found: $port"
            echo "$port"
            return 0
        fi
        log_info "Attempt $i/$max_attempts: Waiting for $svc port..."
        sleep $sleep_time
    done
    
    log_error "Timeout waiting for service '$svc' port"
    echo "pending"
    return 1
}

# Function to wait for service name
wait_for_service_name() {
    local svc=$1
    local max_attempts=60
    local sleep_time=10
    
    log_info "Waiting for service '$svc' name..."
    
    for i in $(seq 1 $max_attempts); do
        name=$(kubectl get svc "$svc" -o jsonpath='{.metadata.name}' 2>/dev/null)
        if [[ -n "$name" ]]; then
            log_info "Service '$svc' name found: $name"
            echo "$name"
            return 0
        fi
        log_info "Attempt $i/$max_attempts: Waiting for $svc name..."
        sleep $sleep_time
    done
    
    log_error "Timeout waiting for service '$svc' name"
    echo "pending"
    return 1
}

# Function to wait for ClusterIP
wait_for_ip() {
    local svc=$1
    local max_attempts=60
    local sleep_time=10
    
    log_info "Waiting for service '$svc' ClusterIP..."
    
    for i in $(seq 1 $max_attempts); do
        ip=$(kubectl get svc "$svc" -o jsonpath='{.spec.clusterIPs[0]}' 2>/dev/null)
        if [[ -n "$ip" && "$ip" != "null" ]]; then
            log_info "Service '$svc' ClusterIP found: $ip"
            echo "$ip"
            return 0
        fi
        log_info "Attempt $i/$max_attempts: Waiting for $svc ClusterIP..."
        sleep $sleep_time
    done
    
    log_error "Timeout waiting for service '$svc' ClusterIP"
    echo "pending"
    return 1
}

# Wait for dataflow server service
SERVICE_NAME="unifai-dataflow-server"

log_info "Retrieving information for service '$SERVICE_NAME'..."

DATAFLOW_ADDR=$(wait_for_ip "$SERVICE_NAME")
DATAFLOW_PORT=$(wait_for_port "$SERVICE_NAME")
DATAFLOW_IP=$(wait_for_service_name "$SERVICE_NAME")

# Validate retrieved values
if [[ "$DATAFLOW_ADDR" == "pending" || "$DATAFLOW_PORT" == "pending" || "$DATAFLOW_IP" == "pending" ]]; then
    log_error "Failed to retrieve all required service information"
    log_error "  DATAFLOW_ADDR: $DATAFLOW_ADDR"
    log_error "  DATAFLOW_PORT: $DATAFLOW_PORT"
    log_error "  DATAFLOW_IP: $DATAFLOW_IP"
    exit 1
fi

log_info "Service information retrieved:"
log_info "  DATAFLOW_ADDR: $DATAFLOW_ADDR"
log_info "  DATAFLOW_PORT: $DATAFLOW_PORT"
log_info "  DATAFLOW_IP: $DATAFLOW_IP"

# Create or update ConfigMap
CONFIGMAP_NAME="unifai-dataflow-config"

log_info "Creating/updating ConfigMap '$CONFIGMAP_NAME'..."

# Delete existing configmap if it exists (ignore if not found)
kubectl delete configmap "$CONFIGMAP_NAME" --ignore-not-found=true

# Create new configmap
kubectl create configmap "$CONFIGMAP_NAME" \
    --from-literal=DATAFLOW_ADDR="$DATAFLOW_ADDR" \
    --from-literal=DATAFLOW_PORT="$DATAFLOW_PORT" \
    --from-literal=DATAFLOW_IP="$DATAFLOW_IP" \
    --dry-run=client -o yaml | kubectl apply -f -

if [[ $? -eq 0 ]]; then
    log_info "ConfigMap '$CONFIGMAP_NAME' created/updated successfully"
else
    log_error "Failed to create/update ConfigMap '$CONFIGMAP_NAME'"
    exit 1
fi

# Verify the configmap was created
if kubectl get configmap "$CONFIGMAP_NAME" &>/dev/null; then
    log_info "Verified: ConfigMap '$CONFIGMAP_NAME' exists"
    
    # Show configmap data for verification
    log_info "ConfigMap contains the following data:"
    kubectl get configmap "$CONFIGMAP_NAME" -o jsonpath='{.data}' | jq '.' 2>/dev/null || kubectl get configmap "$CONFIGMAP_NAME" -o yaml
else
    log_error "Verification failed: ConfigMap '$CONFIGMAP_NAME' not found"
    exit 1
fi

log_info "Postsync hook completed successfully"

