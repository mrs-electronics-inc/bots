#!/bin/bash
# The following environment variables must be included in the
# GitHub Actions job definition:
#    - OPENROUTER_KEY
#    - GITHUB_TOKEN
#    - PULL_REQUEST_NUMBER
# The others are automatically automatically included in GitHub pull request pipelines.
set -e

# I don't know why we need this when it is already in the Dockerfile
# But the GitHub workflow fails otherwise.
git config --global --add safe.directory /repo

export PLATFORM="github"

# Generate the LLM review
generate_llm_review.sh
