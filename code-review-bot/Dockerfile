FROM node:22-slim

SHELL ["/bin/bash", "-c"]

# Install core packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        jq \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Install GitLab CLI
RUN GLAB_VERSION="1.82.0" \
    && curl -fsSL "https://gitlab.com/gitlab-org/cli/-/releases/v${GLAB_VERSION}/downloads/glab_${GLAB_VERSION}_linux_amd64.deb" -o /tmp/glab.deb \
    && dpkg -i /tmp/glab.deb || (apt-get update && apt-get install -y --no-install-recommends -f && rm -rf /var/lib/apt/lists/*) \
    && rm -f /tmp/glab.deb

# Install opencode
RUN npm install -g opencode-ai@latest

# Create skill directories
RUN mkdir -p /root/.config/opencode/skills

# Copy skills
COPY skills/github-code-review /root/.config/opencode/skills/github-code-review
COPY skills/gitlab-code-review /root/.config/opencode/skills/gitlab-code-review

# Copy scripts
COPY should_review.sh /usr/local/bin/
COPY github_code_review.sh /usr/local/bin/
COPY gitlab_code_review.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/should_review.sh /usr/local/bin/github_code_review.sh /usr/local/bin/gitlab_code_review.sh

WORKDIR /workspace

CMD ["/bin/bash"]
