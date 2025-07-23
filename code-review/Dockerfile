# Use the official Python 3.9 slim image as the base
FROM python:3.12-slim

# Install Git and clean up to reduce image size
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install aider
RUN python -m pip install uv \
    && uv tool install --force --python python3.12 --with pip aider-chat@latest

# Make sure aider is in the path
ENV PATH="/root/.local/bin:${PATH}" 

CMD ["/bin/bash"]
