#!/bin/bash

# This script collects context for the code review.
# It expects the following environment variables to be set:
# - PLATFORM: 'gitlab' or 'github'
# - CI_MERGE_REQUEST_PROJECT_ID (if PLATFORM is gitlab)
# - CI_MERGE_REQUEST_IID (if PLATFORM is gitlab)
# - GITHUB_HEAD_REF (if PLATFORM is github)
echo "Collecting context..."

mkdir -p .bots/context

changed_files=""

if [ "$PLATFORM" == "gitlab" ]; then
    # Collect the merge request details
    glab mr view $CI_MERGE_REQUEST_IID > .bots/context/details
    # Collect the merge request comments
    # For some reason the API returns them newest to oldest, so we have to
    # reverse them with jq
    glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes" | jq '[reverse | .[] | {username: .author.username, name: .author.name, timestamp: .created_at, body: .body, id: .id}]' > .bots/context/comments
    # Collect the diffs
    glab mr diff $CI_MERGE_REQUEST_IID --raw > .bots/context/diffs
    # Collect the names of the changed files
    git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    changed_files=$(git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME --name-only)
elif [ "$PLATFORM" == "github" ]; then
    # Collect the pull request details
    gh pr view $GITHUB_HEAD_REF > .bots/context/details
    # Collect the pull request comments
    gh api "repos/$GITHUB_REPOSITORY/issues/$PULL_REQUEST_NUMBER/comments" | jq '[.[] | {username: .user.login, timestamp: .created_at, body: .body, id: .id}]' > .bots/context/comments
    # Collect the diffs
    gh pr diff $GITHUB_HEAD_REF > .bots/context/diffs
    # Collect the names of the changed files
    changed_files=$(gh pr diff $GITHUB_HEAD_REF --name-only)
else
    echo "Error: PLATFORM environment variable must be 'gitlab' or 'github'."
    exit 1
fi

# Run the Python script to collect context into JSON
python3 collect_context.py
