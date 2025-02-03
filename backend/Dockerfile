
# Use the specified Red Hat Universal Base Image 9 (UBI9)
#FROM registry.access.redhat.com/ubi9/python-311
FROM registry.access.redhat.com/ubi9/python-39

#ADD  --chown=1001:1001 . $HOME/backend
ADD  --chown=1001:1001 --chmod=777 ./backend $HOME/backend
ADD  --chown=1001:1001 --chmod=777 ./rag  $HOME/rag
WORKDIR $HOME/backend
RUN chmod 777 .
RUN mkdir $HOME/backend/venv

# update rpms and install debugging tools
USER root
RUN dnf update -y && dnf install -y vim less iputils telnet && dnf clean all
USER 1001
# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv

# Create and activate a virtual environment
RUN virtualenv venv

# Activate the virtual environment and install torch and other required Python packages
RUN /bin/bash -c "source venv/bin/activate && \
    pip install -r requirementsBE.txt && python -m spacy download en_core_web_sm"


# Set the default command to activate the virtual environment and keep the container running
CMD ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]

