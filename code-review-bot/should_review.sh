#!/bin/bash
# should_review.sh — Determine if a full review is needed based on delta analysis.
#
# Usage: should_review.sh <last-reviewed-sha> [current-sha]
#   If last-reviewed-sha is empty, always returns "review needed" (first review).
#   current-sha defaults to HEAD if not provided.
#
# Exit codes:
#   0 = review needed
#   1 = skip review (delta is trivial)
#
# Prints a human-readable reason to stdout.

set -euo pipefail

LAST_REVIEWED_SHA="${1:-}"
CURRENT_SHA="${2:-HEAD}"
DELTA_LINE_THRESHOLD="${DELTA_LINE_THRESHOLD:-20}"

# --- First review: always run ---
if [ -z "$LAST_REVIEWED_SHA" ]; then
    echo "No previous review found. Full review needed."
    exit 0
fi

# --- Can we resolve the old SHA? (force push / rebase) ---
if ! git cat-file -e "$LAST_REVIEWED_SHA" 2>/dev/null; then
    echo "Previous reviewed commit $LAST_REVIEWED_SHA not found (force push or rebase). Full review needed."
    echo "Recent commits available:"
    git log --oneline -10 "$CURRENT_SHA" 2>/dev/null || echo "  (could not list commits)"
    exit 0
fi

# --- Compute delta stats ---
DELTA_STAT=$(git diff --shortstat "$LAST_REVIEWED_SHA" "$CURRENT_SHA" 2>/dev/null || true)
if [ -z "$DELTA_STAT" ]; then
    echo "No changes since last review ($LAST_REVIEWED_SHA). Skipping."
    exit 1
fi

# Extract lines changed (insertions + deletions)
INSERTIONS=$(echo "$DELTA_STAT" | grep -oP '\d+(?= insertion)' || echo 0)
DELETIONS=$(echo "$DELTA_STAT" | grep -oP '\d+(?= deletion)' || echo 0)
TOTAL_LINES=$((INSERTIONS + DELETIONS))

# --- Check delta size ---
if [ "$TOTAL_LINES" -le "$DELTA_LINE_THRESHOLD" ]; then
    echo "Delta is $TOTAL_LINES lines (threshold: $DELTA_LINE_THRESHOLD). Skipping."
    exit 1
fi

# --- Check if only non-code files changed ---
CHANGED_FILES=$(git diff --name-only "$LAST_REVIEWED_SHA" "$CURRENT_SHA")
HAS_CODE_FILES=false
while IFS= read -r file; do
    case "$file" in
        *.md|*.txt|*.json|*.yaml|*.yml|*.toml|*.cfg|*.ini|*.lock|\
        *.csv|*.svg|*.png|*.jpg|*.gif|*.ico|\
        CHANGELOG*|LICENSE*|README*|.gitignore|.gitattributes|\
        .editorconfig|.prettierrc*|.eslintrc*)
            ;; # non-code, skip
        *)
            HAS_CODE_FILES=true
            break
            ;;
    esac
done <<< "$CHANGED_FILES"

if [ "$HAS_CODE_FILES" = false ]; then
    echo "Delta only contains non-code files ($TOTAL_LINES lines). Skipping."
    exit 1
fi

# --- Default: review needed ---
echo "Delta is $TOTAL_LINES lines with code changes. Full review needed."
exit 0
