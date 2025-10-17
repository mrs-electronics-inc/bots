#!/bin/bash
# The following environment variables must be included in the
# GitLab job definition:
#    - GITLAB_TOKEN
#    - PAYLOAD
set -e

export PLATFORM="gitlab"

npx tsx /root/issue-bot-cli.ts "$@"
