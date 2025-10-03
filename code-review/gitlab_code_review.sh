#!/bin/bash
# The following environment variables must be included in the
# GitLab job definition:
#    - OPENROUTER_KEY
#    - GITLAB_TOKEN
# The others are automatically included in GitLab merge request pipelines.
set -e

# Authenticate with GitLab
glab auth login --token $GITLAB_TOKEN

export PLATFORM="gitlab"

# Generate the LLM review
generate_llm_review.sh

# Create or update the review comment
post_review_comment.py
