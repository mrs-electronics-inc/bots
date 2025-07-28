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
RUN llm install llm-openrouter

# Install github CLI (for some reason GitHub Actions doesn't play nice with
# Mise shims).
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update && apt install -y gh;

# Set the working directory - this is where the git repo will be
# mounted in GitLab.
# GitHub sets its own working directory.
WORKDIR /repo
RUN git config --global --add safe.directory /repo

# Add scripts
COPY gitlab_code_review.sh /bin
COPY github_code_review.sh /bin
COPY collect_context.sh /bin
COPY generate_llm_review.sh /bin

CMD ["/bin/bash"]
