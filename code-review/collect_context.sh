#!/bin/bash

# This script collects context for the code review.
# It expects the following environment variables to be set:
# - PLATFORM: 'gitlab' or 'github'
# - CI_MERGE_REQUEST_IID (if PLATFORM is gitlab)
# - GITHUB_HEAD_REF (if PLATFORM is github)

mkdir -p .bots/context

if [ "$PLATFORM" == "gitlab" ]; then
    # Collect the merge request details
    glab mr view $CI_MERGE_REQUEST_IID > .bots/context/merge-request.md
    # Collect the diffs
    glab mr diff $CI_MERGE_REQUEST_IID > .bots/context/diffs.md
    # TODO: include merge request comments in the context

    # Combine context into a single `.bots/context.md` file
    for f in .bots/context/*; do
        echo -e "\n===== BEGIN FILE: $f =====\n"; cat "$f";
    done > .bots/context.md
elif [ "$PLATFORM" == "github" ]; then
    # Collect the pull request details
    gh pr view $GITHUB_HEAD_REF --json body,title,number,url,author,state,createdAt,updatedAt > .bots/context/pull-request.json
    # Collect the diffs
    gh pr diff $GITHUB_HEAD_REF > .bots/context/diffs.md
    # TODO: include pull request comments in the context

    # Combine context into a single `.bots/context.md` file
    # For GitHub, we'll convert the JSON pull request details to a more readable format
    echo "Pull Request Details:" > .bots/context.md
    jq -r '. | to_entries[] | "\(.key): \(.value)"' .bots/context/pull-request.json >> .bots/context.md
    echo -e "\n===== BEGIN FILE: .bots/context/diffs.md =====\n" >> .bots/context.md
    cat .bots/context/diffs.md >> .bots/context.md
else
    echo "Error: PLATFORM environment variable must be 'gitlab' or 'github'."
    exit 1
fi
