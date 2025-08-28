FROM python:3.12-slim

SHELL ["/bin/bash", "-c"]

# Install core packages
RUN apt update \
    && apt install -y git wget gpg curl jq gettext file
 
# Install UV packages and tools
ENV PATH="/root/.local/bin:${PATH}" 
RUN python -m pip install uv \
    && uv pip install --system python-gitlab \
    && uv tool install --force --python python3.12 --with pip aider-chat@latest \
    && uv tool install llm

# Set up llm tool for openrouter
RUN llm install llm-openrouter

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update && apt install -y gh;

# Install GitLab CLI
RUN wget https://gitlab.com/gitlab-org/cli/-/releases/v1.65.0/downloads/glab_1.65.0_linux_amd64.deb \
    && dpkg -i glab_1.65.0_linux_amd64.deb

# Clean up to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# This is where the git repo will be mounted.
WORKDIR /repo
RUN git config --global --add safe.directory /repo

# Add scripts
COPY gitlab_code_review.sh /bin
COPY github_code_review.sh /bin
COPY collect_context.sh /bin
COPY generate_llm_review.sh /bin
COPY generate_llm_review.py /bin
COPY post_gitlab_review_comment.py /bin
COPY system-prompts /bots/system-prompts

CMD ["/bin/bash"]
