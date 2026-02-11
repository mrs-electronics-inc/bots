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

echo "=== GitHub Code Review Bot ==="
echo "PR: #${PULL_REQUEST_NUMBER}"
echo "Model: ${REVIEW_MODEL}"
echo ""

# Build the prompt
PROMPT="Review pull request #${PULL_REQUEST_NUMBER} using the github-code-review skill."

# Run opencode
opencode run \
    --model "$REVIEW_MODEL" \
    --provider openrouter \
    "$PROMPT" \
    2>&1 | tee .bots/review-output.log

echo ""
echo "=== Code review complete ==="
