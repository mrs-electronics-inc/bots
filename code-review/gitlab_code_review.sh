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
collect_context.sh

# Generate the LLM review
generate_llm_review.sh

# NOTE: The "|| true" is because `glab mr note` has an unhandled error,
#       even when the comment posts successfully
# Leave the summary comment if it exists
[ -f .bots/response/summary.md ] && glab mr note $CI_MERGE_REQUEST_IID -m "$(cat .bots/response/summary.md)" || true
# Leave the feedback comment
glab mr note $CI_MERGE_REQUEST_IID -m "$(cat .bots/response/feedback.md)" || true
