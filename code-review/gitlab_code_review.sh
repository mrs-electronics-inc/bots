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
# Leave the review comment
COMMENT_ID="$(cat .bots/context/comments | jq -r 'select(.name == "Code Review Bot") | .id' | tail -n 1)"
echo "Comment ID:"
echo $COMMENT_ID
# AI!: replace this with a python script that uses the gitlab python package to create or update the comment with the contents of .bots/response/review.md
if [ -z "$COMMENT_ID" ] || [ "$COMMENT_ID" == "null" ]; then
  # No old comment to delete
  echo "No old comment to delete"
else 
  # TODO: replace the following with a call to a python script that uses the gitlab API to update the existing comment
  echo "Deleting old comment..."
  echo "PROJECT ID: $CI_MERGE_REQUEST_PROJECT_ID"    
  echo "MERGE REQUEST ID: $CI_MERGE_REQUEST_IID"
  # Delete existing comment
  glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes/$COMMENT_ID" -X DELETE
fi
# Create new comment
glab mr note $CI_MERGE_REQUEST_IID -m "$(cat .bots/response/review.md)" || true
