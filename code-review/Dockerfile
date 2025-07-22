FROM paulgauthier/aider AS aid-core

WORKDIR /app

# Switch to root to install extra dependencies (if needed)
USER root

# Example: install additional tools
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Revert to the standard entrypoint user
USER 1000

# Define default entry command
ENTRYPOINT ["bash"]
CMD ["aider", "--version"]
