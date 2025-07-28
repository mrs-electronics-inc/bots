#!/bin/bash
# The following environment variables must be included in the
# GitHub Actions job definition:
#    - OPENROUTER_KEY
#    - GITHUB_TOKEN
# The others are automatically included in GitHub pull request pipelines.

# Authenticate with GitHub
gh auth login --with-token <<< "$GITHUB_TOKEN"

# Collect all the context
export PLATFORM="github"
./code-review/collect_context.sh

# Generate the LLM review
# TODO: move the summary to a separate multi-line variable
cat .bots/context.md | llm -m summary-model -s "Summarize this pull request. Please note any concerns in the following areas: security, performances, and best practices. For each concern, please include at least one possible solution." > .bots/summary.md

# Leave the comment
gh pr comment $GITHUB_HEAD_REF -F .bots/summary.md
