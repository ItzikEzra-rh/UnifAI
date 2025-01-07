# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi

# Set environment variables
ENV PYTHONUNBUFFERED=1
WORKDIR /app/repo

# Install system dependencies
RUN dnf update -y && \
    dnf install -y python3-pip python3-devel kernel-devel wget which numactl && \
    dnf clean all

# Add application source code
COPY . /app/repo

# Install Python dependencies and setup the package
RUN pip install --upgrade pip && pip install .

# Set entrypoint for the CLI
ENTRYPOINT ["promptlab"]
