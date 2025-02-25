# Use the specified Red Hat Universal Base Image 9 (UBI9)
FROM registry.access.redhat.com/ubi9/python-311
#FROM registry.access.redhat.com/ubi9/python-39
USER root
RUN dnf update -y && dnf install -y vim less iputils telnet && dnf clean all

USER default
ADD  --chown=default:root --chmod=777 ./backend $HOME/backend
ADD  --chown=default:root --chmod=777 ./rag  $HOME/rag
ADD  --chown=default:root --chmod=777 ./pipelines $HOME/pipelines
WORKDIR $HOME/backend
RUN mkdir -p -m 777 $HOME/backend/venv $HOME/backend/logs
RUN ls -lia
RUN chmod -R g+w .

# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv

# Create and activate a virtual environment
RUN virtualenv venv

# Activate the virtual environment and install required Python packages
RUN /bin/bash -c "source venv/bin/activate && \
    pip install -r requirementsBE.txt && \
    python -m spacy download en_core_web_sm"

# Set the default command to activate the virtual environment and keep the container running
CMD ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]

