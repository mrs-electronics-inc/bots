FROM node:lts

SHELL ["/bin/bash", "-c"]

# It is okay to use / as the WORKDIR because Node will automatically look for modules in /.
WORKDIR /

# Copy the package.json and package-lock.json for the CI/CD dev setup
COPY package*.json /

# Install backend dependencies
RUN npm ci --verbose --no-audit --no-fund

# Add backend.
COPY src/* /root
# Add entrypoint script.
COPY gitlab_issue_bot.sh /bin

CMD ["/bin/bash"]
