#!/bin/bash
# GitLab Code Review Bot using OpenCode
#
# Required environment variables:
#   - OPENROUTER_KEY: API key for OpenRouter (also accepts OPENROUTER_API_KEY)
#   - GITLAB_TOKEN: GitLab token for glab CLI
#   - CI_MERGE_REQUEST_IID: MR number (auto-set in GitLab CI)
#
# Optional environment variables:
#   - REVIEW_MODEL: Model to use (default: google/gemini-3-flash-preview)

set -euo pipefail

# Map to the env var OpenRouter expects, preferring the simpler name
export OPENROUTER_API_KEY="${OPENROUTER_KEY:-${OPENROUTER_API_KEY:-}}"

# Validate required environment variables
: "${OPENROUTER_API_KEY:?OPENROUTER_KEY or OPENROUTER_API_KEY is required}"
: "${GITLAB_TOKEN:?GITLAB_TOKEN is required}"
: "${CI_MERGE_REQUEST_IID:?CI_MERGE_REQUEST_IID is required}"

# Set default model if not specified
export REVIEW_MODEL="${REVIEW_MODEL:-google/gemini-3-flash-preview}"

# Authenticate with GitLab
echo "Authenticating with GitLab..."
glab auth login --token "$GITLAB_TOKEN" --hostname gitlab.com

# Create output directory
mkdir -p .bots

echo "=== GitLab Code Review Bot ==="
echo "MR: !${CI_MERGE_REQUEST_IID}"
echo "Model: ${REVIEW_MODEL}"
echo ""

# Build the prompt
PROMPT="Review merge request !${CI_MERGE_REQUEST_IID} using the gitlab-code-review skill."

# Run opencode
opencode run \
    --model "$REVIEW_MODEL" \
    --provider openrouter \
    "$PROMPT" \
    2>&1 | tee .bots/review-output.log

echo ""
echo "=== Code review complete ==="
