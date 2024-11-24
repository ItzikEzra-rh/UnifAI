** Here are the instructions, explaining how to use the Dockerfile of the reviewer component: **

# Building the image
podman build -t reviewer-service .

# To run reviewer worker:
podman run --name celery_worker --gpus all --net=host reviewer-service -d reviewer

# To run reviewer pass/fail worker:
podman run --name celery_worker --gpus all --net=host reviewer-service -d reviewer_pass_fail