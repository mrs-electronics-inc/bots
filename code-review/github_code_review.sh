#!/bin/bash
# The following environment variables must be included in the
# GitHub Actions job definition:
#    - OPENROUTER_KEY
#    - GITHUB_TOKEN
#    - PULL_REQUEST_NUMBER
# The others are automatically automatically included in GitHub pull request pipelines.

# I don't know why we need this when it is already in the Dockerfile
# But the GitHub workflow fails otherwise.
git config --global --add safe.directory /repo

# Collect all the context
export PLATFORM="github"
collect_context.sh

# Generate the LLM review
generate_llm_review.sh

# Leave the summary comment if it exists
[ -f .bots/response/summary.md ] && gh pr comment $GITHUB_HEAD_REF -F .bots/response/summary.md
# Leave the feedback comment
COMMENT_ID="$(cat .bots/response/review.json | jq -r .previous_comment_id)"
echo "Comment ID:"
echo $COMMENT_ID
if [ -z "$COMMENT_ID" ] || [ "$COMMENT_ID" == "null" ]; then
  # Create new comment
  gh pr comment $GITHUB_HEAD_REF -F .bots/response/feedback.md
else
  echo "PR number:"
  echo $PULL_REQUEST_NUMBER
  # Update existing comment
  gh api \
    --method PATCH \
    -H "Accept: application/vnd.github+json" \
    "/repos/${GITHUB_REPOSITORY}/pulls/${PULL_REQUEST_NUMBER}/comments/${COMMENT_ID}" \
    -f body="$(cat ".bots/response/feedback.md")"
fi

