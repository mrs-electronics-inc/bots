FROM python:3.12-slim

SHELL ["/bin/bash", "-c"]

# Install core packages
RUN apt update \
    && apt install -y git wget gpg curl jq gettext file bat
 
# Install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update && apt install -y gh;

# Install GitLab CLI
RUN wget https://gitlab.com/gitlab-org/cli/-/releases/v1.74.0/downloads/glab_1.74.0_linux_amd64.deb \
    && dpkg -i glab_1.74.0_linux_amd64.deb
RUN rm glab_1.74.0_linux_amd64.deb

# Clean up to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# Add scripts
COPY gitlab_code_review.sh /bin
COPY github_code_review.sh /bin
COPY gitlab_tools.py /bin
COPY github_tools.py /bin
COPY tools.py /bin
COPY utils.py /bin
COPY generate_llm_review.sh /bin
COPY generate_llm_review.py /bin
COPY system-prompts /bots/system-prompts

CMD ["/bin/bash"]
