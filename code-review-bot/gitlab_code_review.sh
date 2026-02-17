#!/bin/bash
# GitLab Code Review Bot using OpenCode
#
# Required environment variables:
#   - OPENROUTER_KEY: API key for OpenRouter (also accepts OPENROUTER_API_KEY)
#   - GITLAB_TOKEN: GitLab token for glab CLI
#   - CI_MERGE_REQUEST_IID: MR number (auto-set in GitLab CI)
#   - CI_PROJECT_ID: Project ID (auto-set in GitLab CI)
#
# Optional environment variables:
#   - REVIEW_MODEL: Model to use (default: google/gemini-3-flash-preview)
#   - DELTA_LINE_THRESHOLD: Min lines changed to trigger re-review (default: 20)

set -euo pipefail

# Map to the env var OpenRouter expects, preferring the simpler name
export OPENROUTER_API_KEY="${OPENROUTER_KEY:-${OPENROUTER_API_KEY:-}}"

# Validate required environment variables
: "${OPENROUTER_API_KEY:?OPENROUTER_KEY or OPENROUTER_API_KEY is required}"
: "${GITLAB_TOKEN:?GITLAB_TOKEN is required}"
: "${CI_MERGE_REQUEST_IID:?CI_MERGE_REQUEST_IID is required}"
: "${CI_PROJECT_ID:?CI_PROJECT_ID is required}"

# Set default model if not specified
export REVIEW_MODEL="${REVIEW_MODEL:-google/gemini-3-flash-preview}"

# Authenticate with GitLab
echo "Authenticating with GitLab..."
glab auth login --token "$GITLAB_TOKEN" --hostname gitlab.com

# Create output directory
mkdir -p .bots

# Fix git safe.directory for containers where checkout uid != running uid
git config --global --add safe.directory "$(pwd)"

# Fetch the MR source branch history so we can resolve old reviewed SHAs for delta comparison
git fetch origin "${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-}" --quiet 2>/dev/null || true

echo "=== GitLab Code Review Bot ==="
echo "MR: !${CI_MERGE_REQUEST_IID}"
echo "Model: ${REVIEW_MODEL}"
echo ""

# --- Find existing bot comment and extract last reviewed SHA ---
BOT_NOTE_ID=""
LAST_REVIEWED_SHA=""

echo "Checking for existing bot review..."
# Fetch MR notes via API, look for ones from the bot with our marker
NOTES_JSON=$(glab api "projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes?per_page=100&sort=desc" 2>/dev/null || true)

if [ -n "$NOTES_JSON" ] && [ "$NOTES_JSON" != "null" ]; then
    # Find the most recent note with a reviewed-sha marker from "Code Review Bot" or the CI bot user
    while IFS= read -r note; do
        [ -z "$note" ] && continue
        body=$(echo "$note" | jq -r '.body // ""')
        sha=$(echo "$body" | grep -oP '(?<=<!-- reviewed-sha:)[a-f0-9]+(?= -->)' || true)
        if [ -n "$sha" ]; then
            BOT_NOTE_ID=$(echo "$note" | jq -r '.id')
            LAST_REVIEWED_SHA="$sha"
            break
        fi
    done < <(echo "$NOTES_JSON" | jq -c '.[]')
fi

if [ -n "$LAST_REVIEWED_SHA" ]; then
    echo "Found previous review at commit $LAST_REVIEWED_SHA (note: $BOT_NOTE_ID)"
else
    echo "No previous review found."
fi

# Get the actual MR source branch head SHA
CURRENT_SHA=$(glab api "projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID" | jq -r '.sha')
echo "Current MR head: $CURRENT_SHA"

# --- Check if we should run a full review ---
REVIEW_DECISION=$(should_review.sh "$LAST_REVIEWED_SHA" "$CURRENT_SHA") || REVIEW_EXIT=$?
REVIEW_EXIT=${REVIEW_EXIT:-0}

echo "$REVIEW_DECISION"

if [ $REVIEW_EXIT -ne 0 ]; then
    echo ""
    echo "=== Skipping review ==="
    exit 0
fi

# --- Pre-fetch MR data ---
echo ""
echo "Fetching MR metadata..."
glab mr view "$CI_MERGE_REQUEST_IID" > .bots/mr-metadata.txt

echo "Fetching MR diff..."
glab mr diff "$CI_MERGE_REQUEST_IID" > .bots/mr-diff.txt

echo "Fetching existing comments..."
glab mr view "$CI_MERGE_REQUEST_IID" --comments > .bots/mr-comments.txt 2>/dev/null || true

# Read repo-specific instructions (if present)
REPO_INSTRUCTIONS=""
if [ -f .bots/instructions.md ]; then
    REPO_INSTRUCTIONS=$(cat .bots/instructions.md)
fi

echo "MR data fetched. Starting review..."
echo ""

# --- Build the prompt ---
PROMPT="Review merge request !${CI_MERGE_REQUEST_IID} using the gitlab-code-review skill.

MR data has been pre-fetched to these files:
- .bots/mr-metadata.txt — MR title, author, description, branches
- .bots/mr-diff.txt — full diff
- .bots/mr-comments.txt — existing comments (may be empty)

Start by reading these files. Do NOT re-fetch them with glab CLI.
Write your review to .bots/review-body.md. Do NOT post it yourself."

if [ -n "$REPO_INSTRUCTIONS" ]; then
    PROMPT="${PROMPT}

## Repo-Specific Review Instructions (from .bots/instructions.md)

You MUST follow these instructions:

${REPO_INSTRUCTIONS}"
fi

# --- Run opencode ---
opencode run \
    -m "openrouter/${REVIEW_MODEL}" \
    --thinking \
    --share \
    --print-logs --log-level DEBUG \
    "$PROMPT" \
    2>&1 | tee .bots/review-output.log

# --- Post or update the review comment ---
if [ ! -f .bots/review-body.md ]; then
    echo "ERROR: Agent did not produce .bots/review-body.md"
    exit 1
fi

# Append the reviewed-sha marker using the actual MR source branch head
HEAD_SHA=$(glab api "projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID" | jq -r '.sha')
echo "" >> .bots/review-body.md
echo "<!-- reviewed-sha:${HEAD_SHA} -->" >> .bots/review-body.md

REVIEW_BODY=$(cat .bots/review-body.md)

if [ -n "$BOT_NOTE_ID" ]; then
    echo "Updating existing review note ($BOT_NOTE_ID)..."
    glab api --method PUT \
        "projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes/$BOT_NOTE_ID" \
        -f body="$REVIEW_BODY"
else
    echo "Posting new review note..."
    glab mr note "$CI_MERGE_REQUEST_IID" --message "$REVIEW_BODY"
fi

echo ""
echo "=== Code review complete ==="
