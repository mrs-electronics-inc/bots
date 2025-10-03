#!/bin/bash

# This script collects context for the code review.
# It expects the following environment variables to be set:
# - PLATFORM: 'gitlab' or 'github'
# - CI_MERGE_REQUEST_PROJECT_ID (if PLATFORM is gitlab)
# - CI_MERGE_REQUEST_IID (if PLATFORM is gitlab)
# - GITHUB_HEAD_REF (if PLATFORM is github)
echo "Collecting context..."

mkdir -p .bots/context



if [ "$PLATFORM" == "gitlab" ]; then
    # Collect the merge request comments
    # For some reason the API returns them newest to oldest, so we have to
    # reverse them with jq
    glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes" | jq '[reverse | .[] | {username: .author.username, name: .author.name, timestamp: .created_at, body: .body, id: .id}]' > .bots/context/comments.json


elif [ "$PLATFORM" == "github" ]; then
    # Collect the pull request comments
    gh api "repos/$GITHUB_REPOSITORY/issues/$PULL_REQUEST_NUMBER/comments" | jq '[.[] | {username: .user.login, timestamp: .created_at, body: .body, id: .id}]' > .bots/context/comments.json


else
    echo "Error: PLATFORM environment variable must be 'gitlab' or 'github'."
    exit 1
fi



# Run the Python script to collect context into JSON
collect_context.py
