#!/bin/bash
# GitHub Code Review Bot using OpenCode
#
# Required environment variables:
#   - OPENROUTER_KEY: API key for OpenRouter (also accepts OPENROUTER_API_KEY)
#   - GITHUB_TOKEN: GitHub token for gh CLI (also accepts GH_TOKEN)
#   - PULL_REQUEST_NUMBER: PR number to review
#
# Optional environment variables:
#   - REVIEW_MODEL: Model to use (default: google/gemini-3-flash-preview)

set -euo pipefail

# Map to the env vars the tools expect, preferring the simpler names
export OPENROUTER_API_KEY="${OPENROUTER_KEY:-${OPENROUTER_API_KEY:-}}"
export GH_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

# Validate required environment variables
: "${OPENROUTER_API_KEY:?OPENROUTER_KEY or OPENROUTER_API_KEY is required}"
: "${GH_TOKEN:?GITHUB_TOKEN or GH_TOKEN is required}"
: "${PULL_REQUEST_NUMBER:?PULL_REQUEST_NUMBER is required}"

# Set default model if not specified
export REVIEW_MODEL="${REVIEW_MODEL:-google/gemini-3-flash-preview}"

# Create output directory
mkdir -p .bots

# Fix git safe.directory for containers where checkout uid != running uid
git config --global --add safe.directory "$(pwd)"

echo "=== GitHub Code Review Bot ==="
echo "PR: #${PULL_REQUEST_NUMBER}"
echo "Model: ${REVIEW_MODEL}"
echo ""

# Pre-fetch PR data so the agent doesn't have to figure out CLI flags
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

# Build the prompt
PROMPT="Review pull request #${PULL_REQUEST_NUMBER} using the github-code-review skill.

PR data has been pre-fetched to these files:
- .bots/pr-metadata.json — PR title, author, branches, stats
- .bots/pr-diff.txt — full diff
- .bots/pr-comments.txt — existing comments (truncated)
- .bots/pr-reviews.txt — existing reviews (truncated)

Start by reading these files. Do NOT re-fetch them with gh CLI."

if [ -n "$REPO_INSTRUCTIONS" ]; then
    PROMPT="${PROMPT}

## Repo-Specific Review Instructions (from .bots/instructions.md)

You MUST follow these instructions:

${REPO_INSTRUCTIONS}"
fi

# Run opencode
# Model format: provider/model (e.g. openrouter/google/gemini-3-flash-preview)
opencode run \
    -m "openrouter/${REVIEW_MODEL}" \
    "$PROMPT" \
    2>&1 | tee .bots/review-output.log

echo ""
echo "=== Code review complete ==="
