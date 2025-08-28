#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.
echo "Generating LLM review..."

ls -lah .
echo "---"
ls -lah .bots

# Use the name expected by llm-openrouter
LLM_OPENROUTER_KEY=OPENROUTER_KEY

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review using Python script
generate_llm_review.py

ls -lah .bots/response/review.json

# Add the change requests, if necessary
if [ "$(cat .bots/response/review.json | jq -r '.change_requests')" != "" ]; then
    echo "# Changes Requested" >> .bots/response/review.md
    cat .bots/response/review.json | jq -r ".change_requests" >> .bots/response/review.md
    echo -e "\n\n" >> .bots/response/review.md
fi

# Add the summary, if necessary
if [ "$(cat .bots/response/review.json | jq -r '.summary')" != "" ]; then
    echo "## Summary of Changes" >> .bots/response/review.md
    cat .bots/response/review.json | jq -r ".summary" >> .bots/response/review.md
    echo -e "\n\n" >> .bots/response/review.md
fi

# Add the overall feedback
echo "## Overall Feedback" >> .bots/response/review.md
cat .bots/response/review.json | jq -r ".feedback" >> .bots/response/review.md
echo -e "\n\n" >> .bots/response/review.md
 
# TODO(#15): respond to comments and pipe to .bots/response/comments.md
