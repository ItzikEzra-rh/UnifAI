### ---------------------------- stage 1
FROM docker.io/nvidia/cuda:12.6.0-cudnn-runtime-ubi9 as base

# Install necessary packages
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
RUN dnf update -y && \
    dnf install -y python3-pip git cuda-toolkit  python3-devel

# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv
RUN useradd -ms /bin/bash -d /app appuser
USER appuser
ADD  --chown=1000:1000 . /app

WORKDIR /app
RUN virtualenv venv
ADD  --chown=1000:1000 . /app
RUN /bin/bash -c "source venv/bin/activate &&  pip install -r requirementsBE.txt"

### ---------------------------- stage 2
FROM docker.io/nvidia/cuda:12.6.0-cudnn-runtime-ubi9
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
RUN dnf update -y && \
    dnf install -y git cuda-toolkit python3-devel
RUN dnf clean all
#WORKDIR /root

RUN ln -s /usr/local/cuda-12.6/targets/x86_64-linux/lib/stubs/libcuda.so /usr/lib/libcuda.so
ENV TOKENIZERS_PARALLELISM=true BACKEND_ENV=production

RUN useradd -ms /bin/bash -d /app appuser
USER appuser
ADD  --chown=1000:1000 . /app
WORKDIR /app
COPY --from=base --chown=1000:1000 /app/venv /app/venv
ENV PATH="$PATH:/app/.local/bin"
RUN pip3 install --upgrade pip virtualenv
RUN virtualenv venv
CMD ["/bin/bash", "-c", "cd $HOME && source venv/bin/activate && python app.py"]
