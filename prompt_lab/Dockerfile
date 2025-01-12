# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi

# Set environment variables
ENV PYTHONUNBUFFERED=1
WORKDIR /app/

# Install system dependencies, including a C compiler
RUN dnf update -y && \
    dnf install -y python3-pip python3-devel kernel-devel wget which numactl gcc gcc-c++ make && \
    dnf clean all

# Add application source code
COPY . /app/
RUN ls -R /app/
# Create a virtual environment and activate it
RUN python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install .

# Update PATH to use the virtual environment
ENV PATH="/venv/bin:$PATH"

# Set entrypoint for the CLI
ENTRYPOINT ["promptlab"]
