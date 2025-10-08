FROM node:lts

SHELL ["/bin/bash", "-c"]

# It is okay to use / as the WORKDIR because Node will automatically look for modules in /.
WORKDIR /

# Copy the package.json and package-lock.json for the CI/CD dev setup
COPY package*.json /

# Install dependencies
RUN npm ci --verbose --no-audit --no-fund

# This is where the git repo will be mounted.
WORKDIR /repo
RUN git config --global --add safe.directory /repo

# Add scripts.
COPY issue-bot.ts /bin

CMD ["/bin/bash"]
