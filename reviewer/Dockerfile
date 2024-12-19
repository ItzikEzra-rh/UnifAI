# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HF_TOKEN="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"
ENV GITHUB_TOKEN="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"
# Set working directory
WORKDIR /app

# Install system dependencies
RUN dnf update -y && \
    dnf install -y python3-pip git python3-devel gcc gcc-c++ make cmake kernel-devel wget which numactl gettext \
    && dnf clean all

# Install huggingface_hub before logging in
RUN /bin/bash -c "pip install --upgrade huggingface_hub"

# Clone the repository using token authentication
RUN git clone https://Nirsisr:${GITHUB_TOKEN}@github.com/Nirsisr/AI-TC-s-Generator.git /app/repo

# Login to Hugging Face
RUN /bin/bash -c "huggingface-cli login --token ${HF_TOKEN}"

# Change to repository directory and install dependencies
WORKDIR /app/repo/reviewer

# Install dependencies
RUN /bin/bash -c "pip install --upgrade pip && \
    pip install -r requirements.txt"

# RUN /bin/bash -c "pip install --upgrade pip && \
#     pip install flask-cors websocket-client websockets scapy pymongo uwsgi webargs flask_pymongo pandas celery celery-batches transformers watchdog"

# Create a startup script to run the services
RUN echo '#!/bin/bash' > /app/start-service.sh && \
    echo 'envsubst < config/config.json > config/config.tmp && mv config/config.tmp config/config.json' >> /app/start-service.sh && \
    echo 'case "$1" in' >> /app/start-service.sh && \
    echo '  "reviewer")' >> /app/start-service.sh && \
    echo '    celery -A celery_app.init worker -c 1 --loglevel=info -Q reviewer_queue -n reviewer' >> /app/start-service.sh && \
    echo '    ;;' >> /app/start-service.sh && \
    echo '  "reviewer_pass_fail")' >> /app/start-service.sh && \
    echo '    celery -A celery_app.init worker -c 1 --loglevel=info -Q reviewer_pass_queue,reviewer_fail_queue -n reviewer' >> /app/start-service.sh && \
    echo '    ;;' >> /app/start-service.sh && \
    echo '  "bash")' >> /app/start-service.sh && \
    echo '    bash' >> /app/start-service.sh && \
    echo '    ;;' >> /app/start-service.sh && \
    echo '  *)' >> /app/start-service.sh && \
    echo '    echo "Please specify service: reviewer, or reviewer_pass_fail"' >> /app/start-service.sh && \
    echo '    exit 1' >> /app/start-service.sh && \
    echo '    ;;' >> /app/start-service.sh && \
    echo 'esac' >> /app/start-service.sh && \
    chmod +x /app/start-service.sh

# Set the entrypoint to the startup script
ENTRYPOINT ["/app/start-service.sh"]

# Default command (can be overridden)
CMD ["*"]