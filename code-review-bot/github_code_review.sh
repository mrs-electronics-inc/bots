#!/bin/bash
# GitHub Code Review Bot using OpenCode
#
# Required environment variables:
#   - OPENROUTER_KEY: API key for OpenRouter (also accepts OPENROUTER_API_KEY)
#   - GH_TOKEN: GitHub token for gh CLI
#   - PULL_REQUEST_NUMBER: PR number to review
#
# Optional environment variables:
#   - REVIEW_MODEL: Model to use (default: minimax/minimax-m2.5:nitro)
#   - DELTA_LINE_THRESHOLD: Min lines changed to trigger re-review (default: 20)

set -euo pipefail

# Map to the env vars the tools expect, preferring the simpler names
export OPENROUTER_API_KEY="${OPENROUTER_KEY:-${OPENROUTER_API_KEY:-}}"


# Validate required environment variables
: "${OPENROUTER_API_KEY:?OPENROUTER_KEY or OPENROUTER_API_KEY is required}"
: "${GH_TOKEN:?GH_TOKEN is required}"
: "${PULL_REQUEST_NUMBER:?PULL_REQUEST_NUMBER is required}"

# Set default model if not specified
export REVIEW_MODEL="${REVIEW_MODEL:-minimax/minimax-m2.5:nitro}"

# Create output directory
mkdir -p .bots

# Fix git safe.directory for containers where checkout uid != running uid
git config --global --add safe.directory "$(pwd)"

# Fetch the PR branch history so we can resolve old reviewed SHAs for delta comparison
git fetch origin "pull/${PULL_REQUEST_NUMBER}/head" --quiet 2>/dev/null || true

echo "=== GitHub Code Review Bot ==="
echo "PR: #${PULL_REQUEST_NUMBER}"
echo "Model: ${REVIEW_MODEL}"
echo ""

# --- Find existing bot comment and extract last reviewed SHA ---
BOT_COMMENT_ID=""
LAST_REVIEWED_SHA=""

echo "Checking for existing bot review..."
BOT_COMMENTS=$(gh pr view "$PULL_REQUEST_NUMBER" \
    --json comments \
    --jq '.comments[] | select(.author.login == "github-actions") | {id: .id, body: .body}' \
    2>/dev/null || true)

if [ -n "$BOT_COMMENTS" ]; then
    # Find the most recent comment with a reviewed-sha marker
    while IFS= read -r comment_json; do
        [ -z "$comment_json" ] && continue
        body=$(echo "$comment_json" | jq -r '.body // ""')
        sha=$(echo "$body" | grep -oP '(?<=<!-- reviewed-sha:)[a-f0-9]+(?= -->)' || true)
        if [ -n "$sha" ]; then
            BOT_COMMENT_ID=$(echo "$comment_json" | jq -r '.id // ""')
            LAST_REVIEWED_SHA="$sha"
        fi
    done <<< "$BOT_COMMENTS"
fi

if [ -n "$LAST_REVIEWED_SHA" ]; then
    echo "Found previous review at commit $LAST_REVIEWED_SHA (comment: $BOT_COMMENT_ID)"
else
    echo "No previous review found."
fi

# Get the actual PR branch head SHA (not the merge commit)
CURRENT_SHA=$(gh pr view "$PULL_REQUEST_NUMBER" --json headRefOid --jq '.headRefOid')
echo "Current PR head: $CURRENT_SHA"

# --- Check if we should run a full review ---
REVIEW_DECISION=$(should_review.sh "$LAST_REVIEWED_SHA" "$CURRENT_SHA") || REVIEW_EXIT=$?
REVIEW_EXIT=${REVIEW_EXIT:-0}

echo "$REVIEW_DECISION"

if [ $REVIEW_EXIT -ne 0 ]; then
    echo ""
    echo "=== Skipping review ==="
    exit 0
fi

# --- Pre-fetch PR data ---
echo ""
echo "Fetching PR metadata..."
gh pr view "$PULL_REQUEST_NUMBER" \
    --json number,title,body,author,state,baseRefName,headRefName,additions,deletions,changedFiles \
    > .bots/pr-metadata.json

echo "Fetching PR diff..."
gh pr diff "$PULL_REQUEST_NUMBER" > .bots/pr-diff.txt

echo "Fetching existing comments..."
gh pr view "$PULL_REQUEST_NUMBER" \
    --json comments \
    --jq '.comments[] | "\(.author.login): \(.body[0:200])"' \
    > .bots/pr-comments.txt 2>/dev/null || true

echo "Fetching existing reviews..."
gh pr view "$PULL_REQUEST_NUMBER" \
    --json reviews \
    --jq '.reviews[] | "\(.author.login) (\(.state)): \(.body[0:200])"' \
    > .bots/pr-reviews.txt 2>/dev/null || true

# Read repo-specific instructions (if present)
REPO_INSTRUCTIONS=""
if [ -f .bots/instructions.md ]; then
    REPO_INSTRUCTIONS=$(cat .bots/instructions.md)
fi

echo "PR data fetched. Starting review..."
echo ""

# --- Build the prompt ---
PROMPT="Review pull request #${PULL_REQUEST_NUMBER} using the github-code-review skill.

PR data is attached to this message:
- pr-metadata.json — PR title, author, branches, stats
- pr-diff.txt — full diff
- pr-comments.txt — existing comments (truncated)
- pr-reviews.txt — existing reviews (truncated)

Do NOT re-fetch this data with gh CLI.
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
    --title "Code Review: ${GITHUB_REPOSITORY}#${PULL_REQUEST_NUMBER} @ ${CURRENT_SHA:0:7}" \
    --thinking \
    --share \
    -f .bots/pr-metadata.json \
    -f .bots/pr-diff.txt \
    -f .bots/pr-comments.txt \
    -f .bots/pr-reviews.txt \
    -- "$PROMPT" \
    2>&1 | tee .bots/review-output.log

# --- Post or update the review comment ---
if [ ! -f .bots/review-body.md ]; then
    echo "ERROR: Agent did not produce .bots/review-body.md"
    exit 1
fi

# Extract share link from opencode output
SHARE_LINK=$(grep -oP 'https://opncd\.ai/share/\S+' .bots/review-output.log | head -1 || true)

# Append the reviewed-sha marker using the actual PR branch head (not the merge commit)
HEAD_SHA=$(gh pr view "$PULL_REQUEST_NUMBER" --json headRefOid --jq '.headRefOid')
echo "" >> .bots/review-body.md
if [ -n "$SHARE_LINK" ]; then
    echo "---" >> .bots/review-body.md
    echo "🔗 [OpenCode Session]($SHARE_LINK)" >> .bots/review-body.md
fi
echo "" >> .bots/review-body.md
echo "<!-- reviewed-sha:${HEAD_SHA} -->" >> .bots/review-body.md

REVIEW_BODY=$(cat .bots/review-body.md)

if [ -n "$BOT_COMMENT_ID" ]; then
    echo "Updating existing review comment ($BOT_COMMENT_ID)..."
    # GitHub GraphQL node IDs start with IC_ for issue comments
    gh api graphql -f query='
        mutation($id: ID!, $body: String!) {
            updateIssueComment(input: {id: $id, body: $body}) {
                issueComment { id }
            }
        }' -f id="$BOT_COMMENT_ID" -f body="$REVIEW_BODY"
else
    echo "Posting new review comment..."
    gh pr comment "$PULL_REQUEST_NUMBER" --body "$REVIEW_BODY"
fi

echo ""
echo "=== Code review complete ==="
