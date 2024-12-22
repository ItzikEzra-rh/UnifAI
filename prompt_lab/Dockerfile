# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi

# Set environment variables
ENV PYTHONUNBUFFERED=1
WORKDIR /app/repo/prompt_lab

# Install system dependencies
RUN dnf update -y && \
    dnf install -y python3-pip python3-devel kernel-devel wget which numactl && \
    dnf clean all

# Copy requirements file and install dependencies
COPY requirements.txt /app/repo/prompt_lab/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/repo/prompt_lab/requirements.txt

# Add application source code
COPY . /app/repo/prompt_lab
RUN chmod 755 /app/repo/prompt_lab/start-service.sh

# Set entrypoint
ENTRYPOINT ["/app/repo/prompt_lab/start-service.sh"]
