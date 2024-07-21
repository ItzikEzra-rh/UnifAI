# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/ubi

# Install necessary packages
RUN dnf update -y && \
    dnf install -y python3-pip git && \
    dnf clean all

# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv

# Create and activate a virtual environment
RUN virtualenv /opt/venv

# Activate the virtual environment and install torch and other required Python packages
RUN /bin/bash -c "source /opt/venv/bin/activate && \
    pip install torch && \
    pip install --upgrade pip && \
    pip install git+https://github.com/unslothai/unsloth.git#egg=unsloth[colab-new] && \
    pip install --no-deps 'xformers<0.0.27' 'trl<0.9.0' peft accelerate bitsandbytes"

# Set the default command to activate the virtual environment and keep the container running
CMD ["/bin/bash", "-c", "source /opt/venv/bin/activate && exec bash && sleep infinity"]
