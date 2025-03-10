FROM images.paas.redhat.com/genie/vllm-openai:latest


RUN echo "umask 000" >> /etc/profile

RUN pip3 install --upgrade pip virtualenv
RUN virtualenv venv
ADD . .
RUN /bin/bash -c "source venv/bin/activate &&  pip install -r requirementsBE.txt"


ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV BACKEND_ENV=production
ENV TRITON_CACHE_DIR=/tmp/.triton
ENV VLLM_ENGINE_USE_TCP=1
ENV NCCL_P2P_DISABLE=1
ENV VLLM_CONFIG_ROOT=/tmp/.cache
ENV VLLM_CACHE_ROOT=/tmp/.cache
ENV BACKEND_ENV=production

# Optimize caching & networking
RUN rm -rf /.cache && mkdir /.cache && chmod -R 777 /.cache
RUN mkdir -p /root/.cache/huggingface/ && chmod 777 /root/.cache
ENTRYPOINT ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]
