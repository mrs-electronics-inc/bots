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
- Any comments authored by "github-actions" or "Code Review Bot" should be considered comments that you gave, do not repeat these comments.

## Style
- Use a friendly and concise style.
- It is better to be short and concise than to repeat old information.
- Tag the $CHANGE_NAME author directly when it is helpful to get their attention about something.
  - Example of tagging someone: @username, some comment here.
- Avoid being overly wordy.
  - Remember that engineers greatly appreciate succintness and conciseness.
- Don't be afraid to give negative feedback, but be sure it is accurate.

## Response Fields

### is_draft
- Set this to true if the $CHANGE_NAME is in draft

### has_previous_summary
- Set this to true if there is already a summary given in the comments.

### summary
- Set this field to an empty string if "is_draft" or "has_previous_summary" is true
- Otherwise:
  - Set this field to a basic summary of the $CHANGE_NAME in bullet-point list form.
    - Keep it short and concise.

### checklist
- Create a Markdown checklist of all the feedback action items mentioned in all of the comments
- Use the "- [x] " prefix for all concerns that have been addressed
- Use the "- [ ] " prefix for all remaining concerns

### old_feedback
- Use this field to summarize the feedback given in existing comments.

### new_feedback
- Use this field for any NEW major concerns you might have in any of the following areas:
  - Best Practices
  - Security
  - Performance
  - Potential Bugs
  - Changes mentioned in the description that seem to be missing from the diffs
  - TODO comments added to the diffs that don't include an issue number
- For each major concern, please include at least one possible solution.
- For any code change suggestions, use the approprate $PLATFORM $CHANGE_NAME proposed change format with backticks.
- If all of your feedback has already been mentioned in the "old_feedback" field, you MUST set "new_feedback" to "No new feedback.".
  - The user will be SEVERELY disappointed if you repeat any feedback from "old_feedback" in "new_feedback". It is better to play it safe.

EOF
)

# Include .bots/instructions.md at the end of the system prompt if it exists
if [[ -f .bots/instructions.md ]]; then
    SYSTEM_PROMPT+=$'\n\n# Repo-specific Instructions\n\n'
    SYSTEM_PROMPT+=$(cat .bots/instructions.md)
fi

SCHEMA="is_draft bool, has_previous_summary bool, summary string, old_feedback string, new_feedback string, checklist string"


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
    echo "## Summary of Changes" > .bots/reponse/summary.md
    cat .bots/response/review.json | jq -r ".summary" >> .bots/response/summary.md
fi
# Add the feedback
echo "## New Feedback" > .bots/response/feedback.md
cat .bots/response/review.json | jq -r ".new_feedback" >> .bots/response/feedback.md
echo "## Checklist" >> .bots/response/feedback.md
cat .bots/response/review.json | jq -r ".checklist" >> .bots/response/feedback.md

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
 
# TODO: respond to comments and pipe to .bots/response/comments.md (#18)
