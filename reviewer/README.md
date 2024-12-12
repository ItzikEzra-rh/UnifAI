** Here are the instructions, explaining how to use the Dockerfile of the reviewer component: **

# Building the image
podman build -t reviewer-service .

# To run reviewer worker:
```bash
podman run --name celery_worker --gpus all --net=host \
  -e RABBITMQ_PORT="$RABBITMQ_PORT" \
  -e RABBITMQ_IP="$RABBITMQ_IP" \
  -e MONGODB_PORT="$MONGODB_PORT" \
  -e MONGODB_IP="$MONGODB_IP" \
  reviewer-service reviewer

```

# To run reviewer pass/fail worker:
```bash
# To run reviewer pass/fail worker:
podman run --name celery_worker --gpus all --net=host \
  -e RABBITMQ_PORT="$RABBITMQ_PORT" \
  -e RABBITMQ_IP="$RABBITMQ_IP" \
  -e MONGODB_PORT="$MONGODB_PORT" \
  -e MONGODB_IP="$MONGODB_IP" \
  reviewer-service reviewer_pass_fail

```