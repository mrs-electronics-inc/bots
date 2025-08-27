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
    glab api "projects/$CI_MERGE_REQUEST_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes" | jq 'reverse | .[] | {username: .author.username, name: .author.name, timestamp: .created_at, body: .body, id: .id}' > .bots/context/comments
    # Collect the diffs
    glab mr diff $CI_MERGE_REQUEST_IID --raw > .bots/context/diffs
    # Collect the names of the changed files
    git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    changed_files=$(git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME --name-only)
elif [ "$PLATFORM" == "github" ]; then
    # Collect the pull request details
    gh pr view $GITHUB_HEAD_REF > .bots/context/details
    # Collect the pull request comments
    gh api "repos/$GITHUB_REPOSITORY/issues/$PULL_REQUEST_NUMBER/comments" | jq '.[] | {username: .user.login, timestamp: .created_at, body: .body, id: .id}' > .bots/context/comments
    # Collect the diffs
    gh pr diff $GITHUB_HEAD_REF > .bots/context/diffs
    # Collect the names of the changed files
    changed_files=$(gh pr diff $GITHUB_HEAD_REF --name-only)
else
    echo "Error: PLATFORM environment variable must be 'gitlab' or 'github'."
    exit 1
fi

context_files=("details" "diffs" "comments")
# Combine context into a single `.bots/context.md` file
for f in "${context_files[@]}"; do
    echo -e "\n\n===== BEGIN CONTEXT: $f =====\n\n"; cat ".bots/context/$f"; echo -e "\n\n===== END CONTEXT: $f =====\n\n"
done > .bots/context.md

echo -e "changed files:\n$changed_files"
if [ -z "$changed_files" ]; then
    echo "Warning: No changed files detected."
fi
count=0
max_count=10
# Iterate through each changed file
while IFS= read -r file; do
    # Check if the file exists
    if [[ -f "$file" ]]; then
        # Count the number of lines in the file
        line_count=$(wc -l < "$file")
        # Check if the line count is less than 400
        if (( line_count < 400 )); then
            echo "===== BEGIN FILE: $file =====" >> .bots/context.md;
            cat "$file" >> .bots/context.md;
            echo "===== END FILE: $file =====" >> .bots/context.md
            ((count++))
            # Exit early if max_count reached
            if (( count >= max_count )); then
                break
            fi
        fi
    fi
done <<< "$changed_files"
