#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.
echo "Generating LLM review..."

REVIEW_MODEL=openrouter/qwen/qwen3-coder
export CHANGE_NAME=$([ "$PLATFORM" = "github" ] && echo "pull request" || echo "merge request")
envsubst < system-prompts/generate-feedback.md > .bots/system-prompt.md

# Include .bots/instructions.md at the end of the system prompt if it exists
echo $'\n\n# Repo-specific Instructions\n\n' >> .bots/system-prompt.md
if [[ -f .bots/instructions.md ]]; then
    cat .bots/instructions.md >> .bots/system-prompt.md
else
    echo 'None.' >> .bots/system-prompt.md
fi

# Read the system prompt while preserving newlines
SYSTEM_PROMPT=$(cat .bots/system-prompt.md)

SCHEMA="is_draft bool, has_previous_summary bool, summary string, raw_feedback string, feedback string"


# This shouldn't be necessary, but without it the `llm` tool won't
# recognize openrouter models.
# https://github.com/simonw/llm-openrouter/issues/34
llm keys set openrouter --value "$OPENROUTER_KEY"

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review
cat .bots/context.md | llm -m $REVIEW_MODEL -o presence_penalty 1.5 -o temperature 1.1 -s "$SYSTEM_PROMPT" --schema "$SCHEMA" > .bots/response/review.json

# Add the summary, if necessary
if [ "$(cat .bots/response/review.json | jq -r '.summary')" != "" ]; then
    echo "## Summary of Changes" > .bots/response/summary.md
    cat .bots/response/review.json | jq -r ".summary" >> .bots/response/summary.md
fi

# Add the feedback
echo "## Feedback" > .bots/response/feedback.md
cat .bots/response/review.json | jq -r ".feedback" >> .bots/response/feedback.md

# These are for debugging
echo "================================"
echo -e "System Prompt:\n$SYSTEM_PROMPT"
echo "================================"
echo -e "Context:\n$(cat .bots/context.md)"
echo "================================"
echo -e "Review JSON:\n$(cat .bots/response/review.json)"
[ -f .bots/response/summary.md ] && echo "================================"
[ -f .bots/response/summary.md ] && echo -e "Summary Markdown:\n$(cat .bots/response/summary.md)"
echo "================================"
echo -e "Feedback Markdown:\n$(cat .bots/response/feedback.md)"
echo "================================"
 
# TODO: respond to comments and pipe to .bots/response/comments.md (#15)
