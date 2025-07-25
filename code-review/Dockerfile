FROM python:3.12-slim

SHELL ["/bin/bash", "-c"]

# Install core packages
RUN apt update \
    && apt install -y git wget gpg curl

# Prep for Mise
RUN wget -qO - https://mise.jdx.dev/gpg-key.pub | gpg --dearmor | tee /etc/apt/keyrings/mise-archive-keyring.gpg 1> /dev/null \
    && echo "deb [signed-by=/etc/apt/keyrings/mise-archive-keyring.gpg arch=amd64] https://mise.jdx.dev/deb stable main" | tee /etc/apt/sources.list.d/mise.list

# Install Mise
RUN apt update \
    && apt install -y mise

# Clean up to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# Install Mise tools
# We must use shims since we aren't using mise in an interactive shell
ENV PATH="/root/.local/share/mise/shims:${PATH}"
RUN mise use -g glab@1.64.0

# Install UV tools
ENV PATH="/root/.local/bin:${PATH}" 
RUN python -m pip install uv \
    && uv tool install --force --python python3.12 --with pip aider-chat@latest \
    && uv tool install llm

# Set up llm tool for openrouter
RUN llm install llm-openrouter \
    && llm aliases set summary-model openrouter/google/gemini-2.5-flash-lite

# Set the working directory - this is where the git repo will be mounted
RUN mkdir /repo
WORKDIR /repo
RUN git config --global --add safe.directory /repo

# Add scripts
COPY gitlab_code_review.sh /bin

CMD ["/bin/bash"]
