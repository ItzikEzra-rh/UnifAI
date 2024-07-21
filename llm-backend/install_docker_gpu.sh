#!/bin/bash

# Remove any existing Docker installations
sudo yum remove -y docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine \
                  podman \
                  runc

# Install yum-utils
sudo yum install -y yum-utils

# Add Docker's official repository
sudo yum-config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo

# Install Docker CE and related packages
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Install NVIDIA Container Toolkit
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

sudo yum install -y nvidia-container-toolkit

# Configure NVIDIA Container Toolkit for Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker service to apply changes
sudo systemctl restart docker

echo "Docker and NVIDIA Container Toolkit installation completed."
