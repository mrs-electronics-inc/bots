#!/bin/bash

# This script collects context for the code review.
# It expects the following environment variables to be set:
# - PLATFORM: 'gitlab' or 'github'
# - CI_MERGE_REQUEST_PROJECT_ID (if PLATFORM is gitlab)
# - CI_MERGE_REQUEST_IID (if PLATFORM is gitlab)
# - GITHUB_HEAD_REF (if PLATFORM is github)

mkdir -p .bots/context

if [ "$PLATFORM" == "gitlab" ]; then
    # Collect the merge request details
    glab mr view $CI_MERGE_REQUEST_IID > .bots/context/details
    # Collect the merge request comments
    glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes" | jq '.[] | {username: .author.username, timestamp: .created_at, body: .body}' > .bots/context/comments
    # Collect the diffs
    glab mr diff $CI_MERGE_REQUEST_IID > .bots/context/diffs
elif [ "$PLATFORM" == "github" ]; then
    # Collect the pull request details
    gh pr view $GITHUB_HEAD_REF > .bots/context/details
    # Collect the pull request comments
    gh pr view $GITHUB_HEAD_REF --comments > .bots/context/comments
    # Collect the diffs
    gh pr diff $GITHUB_HEAD_REF > .bots/context/diffs
else
    echo "Error: PLATFORM environment variable must be 'gitlab' or 'github'."
    exit 1
fi

echo "Combining context"
context_files=("details" "diffs" "comments")
# Combine context into a single `.bots/context.md` file
for f in "${context_files[@]}"; do
    echo -e "\n\n===== BEGIN CONTEXT: $f =====\n\n"; cat ".bots/context/$f"; echo -e "\n\n===== END CONTEXT: $f =====\n\n"
done > .bots/context.md
