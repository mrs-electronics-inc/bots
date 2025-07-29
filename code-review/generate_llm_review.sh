#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.

REVIEW_MODEL=openrouter/google/gemini-2.5-flash
CHANGE_NAME=$([ "$PLATFORM" = "github" ] && echo "pull request" || echo "merge request")
SYSTEM_PROMPT=$(cat <<EOF
# Background
- You are a helpful and experienced software engineer who will review this $PLATFORM $CHANGE_NAME.
  - The $CHANGE_NAME description and details are available in ".bots/context/details".
  - The $CHANGE_NAME comments are available in ".bots/context/comments".
  - The git diffs are available in ".bots/context/diffs".
  - Don't directly mention any of the filenames from the ".bots" directory. These are added for your context only. They do not exist in the real codebase.
  - Be sure to use proper Markdown formatting in your responses, including headings and subheading when appropriate.
- Give a basic summary of the changes, but ONLY if none of the previous comments include a summary of the changes.
  - Be sure to highlight any changes mentioned in the description that seem to be missing from the diffs. Perhaps the developer forgot to do some of the changes that they intended to do.
  - Be sure to highlight any TODO comments added in the diffs. Perhaps the developer forgot to do some of the changes that they intended to do.
- BE SURE not to repeat feedback given in the existing review comments.- Double check all of your new feedback to make sure it DOES NOT repeat previous feedback.
- If you have nothing to say, respond with "No new feedback."
- Please note any major concerns in the following areas:
  - Best Practices
  - Security
  - Performance
  - Potential Bugs
- Leave out any concern areas that have no major concerns.
- For each major concern, please include at least one possible solution.
- Don't be afraid to give negative feedback, but be sure it is accurate.
EOF
)

# Include .bots/instructions.md at the end of the system prompt if it exists
if [[ -f .bots/instructions.md ]]; then
    SYSTEM_PROMPT+="\n\n # Repo-specific Instructions\n\n"
    SYSTEM_PROMPT+=$(<.bots/instructions.md)
fi

# These are for debugging
echo "================================"
echo "System Prompt:\n$SYSTEM_PROMPT"
echo "================================"
echo "Context:\n$(cat .bots/context.md)"
echo "================================"

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
