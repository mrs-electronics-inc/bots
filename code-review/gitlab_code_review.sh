#!/bin/bash
# The following environment variables must be included in the
# GitLab job definition:
#    - OPENROUTER_KEY
#    - GITLAB_TOKEN
# The others are automatically included in GitLab merge request pipelines.

# Authenticate with GitLab
glab auth login --token $GITLAB_TOKEN

# Collect all the context
export PLATFORM="gitlab"
./code-review/collect_context.sh

# Generate the LLM review
# TODO: move the summary to a separate multi-line variable
cat .bots/context.md | llm -m summary-model -s "Summarize this merge request. Please note any concerns in the following areas: security, performances, and best practices. For each concern, please include at least one possible solution." > .bots/summary.md

# Leave the comment
# NOTE: The "|| true" is because `glab mr note` has an unhandled error,
#       even when the comment posts successfully
glab mr note $CI_MERGE_REQUEST_IID -m "$(cat .bots/summary.md)" || true
