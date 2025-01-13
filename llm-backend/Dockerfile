### ---------------------------- stage 1
FROM docker.io/nvidia/cuda:12.6.0-cudnn-runtime-ubi9 as base

# Install necessary packages
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
RUN dnf update -y && \
    dnf install -y python3-pip git cuda-toolkit  python3-devel

# Upgrade pip and install virtualenv
RUN pip3 install --upgrade pip virtualenv
#WORKDIR /root
# Create and activate a virtual environment
RUN virtualenv venv
# Activate the virtual environment and install torch and other required Python packages
#RUN /bin/bash -c "source venv/bin/activate && \
#    pip install --upgrade pip && \
#    pip install torch==2.3.0 transformers==4.38 && \
#    pip install --upgrade --force-reinstall --no-cache-dir torch==2.3.0 triton --index-url https://download.pytorch.org/whl/cu121 && \
#    pip install git+https://github.com/unslothai/unsloth.git#egg=unsloth[colab-new] && \
#    pip install -U xformers --index-url https://download.pytorch.org/whl/cu121 && \
#    pip install --no-deps 'trl<0.9.0' peft accelerate bitsandbytes"

ADD . .
RUN /bin/bash -c "source venv/bin/activate &&  pip install -r requirementsBE.txt"

### ---------------------------- stage 2
FROM docker.io/nvidia/cuda:12.6.0-cudnn-runtime-ubi9
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
RUN dnf update -y && \
    dnf install -y git cuda-toolkit python3-devel
RUN dnf clean all
#WORKDIR /root
COPY --from=base venv venv

ADD . .
RUN ln -s /usr/local/cuda-12.6/targets/x86_64-linux/lib/stubs/libcuda.so /usr/lib/libcuda.so
ENV TOKENIZERS_PARALLELISM=true BACKEND_ENV=development
CMD ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]

