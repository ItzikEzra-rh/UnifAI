** Here are the instructions, explaining how to use the Dockerfile of the reviewer component: **

# Building the image
podman build -t reviewer-service .

# To run reviewer worker:
podman run --gpus all reviewer-service reviewer

# To run reviewer pass/fail worker:
podman run --gpus all reviewer-service reviewer_pass_fail