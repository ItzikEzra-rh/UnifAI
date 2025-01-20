# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/python-39

ADD . $HOME
WORKDIR $HOME
RUN mkdir $HOME/venv

# update rpms and install debugging tools
RUN dnf update -y && dnf install -y vim iputils telnet && dnf clean all
# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv

# Create and activate a virtual environment
RUN virtualenv $HOME/venv

# Activate the virtual environment and install torch and other required Python packages
RUN /bin/bash -c "source $HOME/venv/bin/activate && \
    pip install -r requirementsBE.txt"

# Set the default command to activate the virtual environment and keep the container running
CMD ["/bin/bash", "-c", "source $HOME/venv/bin/activate && python app.py"]

