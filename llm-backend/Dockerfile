### ---------------------------- stage 1
FROM docker.io/nvidia/cuda:12.6.0-cudnn-runtime-ubi9 as base

# Install necessary packages
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
RUN dnf update -y && \
    dnf install -y python3-pip git cuda-toolkit  python3-devel

# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv

# Create and activate a virtual environment
RUN virtualenv venv

ADD . .
RUN /bin/bash -c "source venv/bin/activate &&  pip install -r requirementsBE.txt"

### ---------------------------- stage 2
FROM docker.io/nvidia/cuda:12.6.0-cudnn-runtime-ubi9
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
RUN dnf update -y && \
    dnf install -y git cuda-toolkit python3-devel vim less iputils telnet
RUN dnf clean all
#WORKDIR /root
COPY --from=base venv venv

ADD . .
RUN ln -s /usr/local/cuda-12.6/targets/x86_64-linux/lib/stubs/libcuda.so /usr/lib/libcuda.so
ENV TOKENIZERS_PARALLELISM=true BACKEND_ENV=production
CMD ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]
