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
# TODO: get comment ID
COMMENT_ID="$(cat .bots/response/review.json | jq -r .previous_comment_id)"
# TODO: create new comment if comment ID is null
glab mr note $CI_MERGE_REQUEST_IID -m "$(cat .bots/response/feedback.md)" || true
# TODO: update previous comment correct
glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_ID/notes/$COMMENT_ID -X PUT -F "$(cat .bots/response/feedback.md)"
