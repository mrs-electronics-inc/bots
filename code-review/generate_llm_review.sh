#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.

REVIEW_MODEL=openrouter/google/gemini-2.5-flash
SYSTEM_PROMPT=$(cat <<EOF
- You will review this pull/merge request.
- BE SURE not to repeat feedback given in the existing review comments.- Double check all of your new feedback to make sure it DOES NOT repeat previous feedback.
- If you have nothing else to say, respond with "No new feedback."
- Please note any major concerns in the following areas:
  - Best Practices
  - Security
  - Performance
  - Potential Bugs
- Leave out any concern areas that have no major concerns.
- For each major concern, please include at least one possible solution.
- Don't be afraid to give negative feedback, but be sure it is accurate.
- Don't directly mention any of the filenames from the ".bots" directory. These are added for your context only. They do not exist in the real codebase.
EOF
)
# TODO: include .bots/instructions.md at the end of the system prompt if it exists

# This shouldn't be necessary, but without it the `llm` tool won't
# recognize openrouter models.
# https://github.com/simonw/llm-openrouter/issues/34
llm keys set openrouter --value "$OPENROUTER_KEY"

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review
cat .bots/context.md | llm -m $REVIEW_MODEL -s "$SYSTEM_PROMPT" > .bots/response/review.md

# TODO: respond to comments and pipe to .bots/response/comments.md
