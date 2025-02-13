# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi

# Set environment variables
ENV PYTHONUNBUFFERED=1

WORKDIR /app/repo/reviewer

# Install system dependencies
RUN dnf update -y && \
    dnf install -y python3-pip python3-devel kernel-devel wget which numactl vim less iputils telnet gettext && \
    dnf clean all

# Copy application source code
COPY . /app/repo/reviewer
RUN chmod 755 /app/repo/reviewer/start-service.sh

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r /app/repo/reviewer/requirements.txt

RUN mkdir -p /app/repo/reviewer/data && chmod -R  777 /app/repo/
RUN mkdir /.cache && chmod 777 /.cache

# Set entrypoint
ENTRYPOINT ["/app/repo/reviewer/start-service.sh"]

# Default command (can be overridden)
CMD ["*"]
