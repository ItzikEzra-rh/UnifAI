FROM images.paas.redhat.com/genie/vllm-openai:latest

# Install dependencies
RUN pip install hf_transfer nvitop llmcompressor

RUN echo "umask 000" >> /etc/profile

ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV MPLCONFIGDIR=/tmp/matplotlib

# Optimize caching & networking
RUN rm -rf /.cache && mkdir /.cache && chmod -R 777 /.cache
RUN mkdir -p /root/.cache/huggingface/ && chmod 777 /root/.cache