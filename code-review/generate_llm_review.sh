#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.
echo "Generating LLM review..."

REVIEW_MODEL=openrouter/google/gemini-2.5-flash
CHANGE_NAME=$([ "$PLATFORM" = "github" ] && echo "pull request" || echo "merge request")
SYSTEM_PROMPT=$(cat <<EOF
# Background
 
## Persona
- You are a helpful senior software engineer who will review this $PLATFORM $CHANGE_NAME.
  - The user will refer to you as the "code review bot"
  - Please carefully review the $CHANGE_NAME details and comments. Also take a look at the git diffs.
  - The current contents of several of the changed files are also included in your context. Only files under 400 lines are included, and only a maximum of 10 files are included.
  - Follow the given JSON schema for your output.
    - A post-processing tool will convert each field into its own Markdown section in the final output.
    - Use an empty string for any fields where appropriate.

## Avoid Repetition
- Any comments authored by "github-actions" or "Code Review Bot" should be considered comments that you gave, do not repeat these comments.
- BE SURE not to repeat feedback given in any of the existing comments.
  - Double check all of your new feedback to make sure it DOES NOT repeat information from the existing comments.
  - DO NOT repeat any details that were already discussed in the comments.
- It is better to be short and concise than to repeat old information.

## Style
- Use a friendly and concise style.
- Tag the $CHANGE_NAME author directly when it is helpful to get their attention about something.
  - Example of tagging someone: @username, some comment here.
- Avoid being overly wordy.
  - Remember that engineers greatly appreciate succintness and conciseness.
- Don't be afraid to give negative feedback, but be sure it is accurate.

## Summarize Changes
- Give a basic summary of the changes in the "summary" field of the JSON.
  - Set "previous_summary" to true if there is already a summary given in the comments.
  - Use an empty string for the "summary" field if "previous_summary" is true.
  - Otherwise:
    - Be sure to highlight any changes mentioned in the description that seem to be missing from the diffs. Perhaps the developer forgot to do some of the changes that they intended to do.
    - Be sure to highlight any TODO comments added in the diffs. Perhaps the developer forgot to do some of the changes that they intended to do.

## Major Concerns
- Please note any major concerns in the following areas:
  - Best Practices
  - Security
  - Performance
  - Potential Bugs
- Leave out any concern areas that have no major concerns.
- For each major concern, please include at least one possible solution.
- For any code change suggestions, use the approprate $PLATFORM $CHANGE_NAME proposed change format with backticks.

## Resolved Concerns
- Briefly mention concerns that were mentioned in previous comments but now appear to be resolved in the current version of the $CHANGE_NAME under a "## Resolved Concerns" section at the end of your response.
- Leave this section out if it doesn't apply.
EOF
)

# Include .bots/instructions.md at the end of the system prompt if it exists
if [[ -f .bots/instructions.md ]]; then
    SYSTEM_PROMPT+=$'\n\n# Repo-specific Instructions\n\n'
    SYSTEM_PROMPT+=$(cat .bots/instructions.md)
fi

SCHEMA="review string, summary string, previous_summary bool"


# This shouldn't be necessary, but without it the `llm` tool won't
# recognize openrouter models.
# https://github.com/simonw/llm-openrouter/issues/34
llm keys set openrouter --value "$OPENROUTER_KEY"

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review
cat .bots/context.md | llm -m $REVIEW_MODEL -o presence_penalty 1.1 -o temperature 1.1 -s "$SYSTEM_PROMPT" --schema "$SCHEMA" > .bots/response/review.json

# TODO: pull out different fields from the response JSON into different MD files
# AI!: add ".summary" field from JSON to review.md, if ".previous_summary" field is false
cat .bots/response/review.json | jq -r ".review" >> .bots/response/review.md

# These are for debugging
echo "================================"
echo -e "System Prompt:\n$SYSTEM_PROMPT"
echo "================================"
echo -e "Context:\n$(cat .bots/context.md)"
echo "================================"
echo -e "Review JSON:\n$(cat .bots/response/review.json)"
echo "================================"
echo -e "Review Markdown:\n$(cat .bots/response/review.md)"
echo "================================"
 
# TODO: respond to comments and pipe to .bots/response/comments.md
