#!/bin/bash
# The following environment variables must be included in the
# GitHub Actions job definition:
#    - OPENROUTER_KEY
#    - GITHUB_TOKEN
# The others are automatically automatically included in GitHub pull request pipelines.

# Authenticate with GitHub
gh auth login --with-token <<< "$GITHUB_TOKEN"

# Collect all the context
export PLATFORM="github"
collect_context.sh

# Generate the LLM review
generate_llm_review.sh

# Leave the comment
gh pr comment $GITHUB_HEAD_REF -F .bots/summary.md
