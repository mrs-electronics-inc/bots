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

# Fix git safe.directory for containers where checkout uid != running uid
git config --global --add safe.directory "$(pwd)"

echo "=== GitLab Code Review Bot ==="
echo "MR: !${CI_MERGE_REQUEST_IID}"
echo "Model: ${REVIEW_MODEL}"
echo ""

# Pre-fetch MR data so the agent doesn't have to figure out CLI flags
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

# Build the prompt
PROMPT="Review merge request !${CI_MERGE_REQUEST_IID} using the gitlab-code-review skill.

MR data has been pre-fetched to these files:
- .bots/mr-metadata.txt — MR title, author, description, branches
- .bots/mr-diff.txt — full diff
- .bots/mr-comments.txt — existing comments (may be empty)

Start by reading these files. Do NOT re-fetch them with glab CLI."

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
