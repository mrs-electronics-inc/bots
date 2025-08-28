#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.
echo "Generating LLM review..."

export CHANGE_NAME=$([ "$PLATFORM" = "github" ] && echo "pull request" || echo "merge request")
envsubst < /bots/system-prompts/review.md > .bots/system-prompt.md

# Include .bots/instructions.md at the end of the system prompt if it exists
echo $'\n\n# Repo-specific Instructions\n\n' >> .bots/system-prompt.md
if [[ -f .bots/instructions.md ]]; then
    cat .bots/instructions.md >> .bots/system-prompt.md
else
    echo 'None.' >> .bots/system-prompt.md
fi

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review using Python script
python3 code-review/generate_llm_review.py

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

# These are for debugging
echo "================================"
echo -e "System Prompt:\n$(cat .bots/system-prompt.md)"
echo "================================"
echo -e "Context:\n$(cat .bots/context.md)"
echo "================================"
echo -e "Review JSON:\n$(cat .bots/response/review.json)"
echo "================================"
echo -e "Review Markdown:\n$(cat .bots/response/review.md)"
echo "================================"
 
# TODO(#15): respond to comments and pipe to .bots/response/comments.md
