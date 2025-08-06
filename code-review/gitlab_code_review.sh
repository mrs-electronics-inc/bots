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
COMMENT_ID="$(cat .bots/context/comments | jq -r 'select(.name == "Code Review Bot") | .id' | tail -n 1)"
echo "Comment ID:"
echo $COMMENT_ID
if [ -z "$COMMENT_ID" ] || [ "$COMMENT_ID" == "null" ]; then
  # Create new comment
  glab mr note $CI_MERGE_REQUEST_IID -m "$(cat .bots/response/feedback.md)" || true
else 
  # Update existing comment
  glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_ID/notes/$COMMENT_ID" -X PUT -F "$(cat .bots/response/feedback.md)"
fi
