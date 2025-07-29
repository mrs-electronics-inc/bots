#!/bin/bash

# This script collects context for the code review.
# It expects the following environment variables to be set:
# - PLATFORM: 'gitlab' or 'github'
# - CI_MERGE_REQUEST_IID (if PLATFORM is gitlab)
# - GITHUB_HEAD_REF (if PLATFORM is github)

mkdir -p .bots/context

if [ "$PLATFORM" == "gitlab" ]; then
    # Collect the merge request details
    glab mr view $CI_MERGE_REQUEST_IID > .bots/context/details
    # Collect the merge request comments
    glab api "https://gitlab.com/api/v4/projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes" > .bots/context/comments
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
# Combine context into a single `.bots/context.md` file
for f in .bots/context/*; do
    echo -e "\n===== BEGIN FILE: $f =====\n"; cat "$f";
done > .bots/context.md
