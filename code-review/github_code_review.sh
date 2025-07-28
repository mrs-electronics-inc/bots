#!/bin/bash
# The following environment variables must be included in the
# GitHub Actions job definition:
#    - OPENROUTER_KEY
#    - GITHUB_TOKEN
# The others are automatically automatically included in GitHub pull request pipelines.

# Trust the current directory
git config --global --add safe.directory "$(pwd)"

echo "Hello world!"

gh --version

# Collect all the context
export PLATFORM="github"
collect_context.sh

echo "Context collected!"

# Generate the LLM review
generate_llm_review.sh

echo "Code review generated!"

# Leave the comment
gh pr comment $GITHUB_HEAD_REF -F .bots/summary.md
