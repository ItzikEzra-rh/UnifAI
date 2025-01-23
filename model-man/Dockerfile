# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi
RUN dnf update -y && dnf install -y git-lfs
WORKDIR /data/models
CMD git clone https://${HUGGING_FACE_HUB_USER}:${HUGGING_FACE_HUB_TOKEN}@huggingface.co/${GENIE_MODEL_NAME} 
