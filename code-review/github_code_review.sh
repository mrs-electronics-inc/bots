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

# Leave the review comment
# Find existing review comment from Code Review Bot
REVIEW_COMMENT_ID=$(gh pr comments $GITHUB_HEAD_REF --json id,body,author | jq -r '.[] | select(.author.login == "github-actions[bot]" or .author.login == "Code Review Bot") | select(.body | startswith("# Changes Requested") or startswith("## Summary") or startswith("## Overall Feedback")) | .id' | head -1)

if [ -n "$REVIEW_COMMENT_ID" ]; then
    echo "Updating existing review comment with ID: $REVIEW_COMMENT_ID"
    gh pr comment $GITHUB_HEAD_REF --edit $REVIEW_COMMENT_ID -F .bots/response/review.md
else
    echo "Creating new review comment"
    gh pr comment $GITHUB_HEAD_REF -F .bots/response/review.md
fi

# Leave comment responses if they exist
if [ -f ".bots/response/comments.md" ] && [ -s ".bots/response/comments.md" ]; then
    echo "Posting comment responses..."
    gh pr comment $GITHUB_HEAD_REF --body "$(cat .bots/response/comments.md)"
fi
