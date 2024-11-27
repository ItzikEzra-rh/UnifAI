** Here are the instructions, explaining how to use the Dockerfile of the reviewer component: **

# Building the image
podman build -t reviewer-service .

# To run reviewer worker:
podman run --name celery_worker --gpus all --net=host reviewer-service reviewer

# To run reviewer pass/fail worker:
podman run --name celery_worker --gpus all --net=host reviewer-service reviewer_pass_fail