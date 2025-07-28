#!/bin/bash
# The following environment variables must be included in the
# GitHub Actions job definition:
#    - OPENROUTER_KEY
#    - GITHUB_TOKEN
# The others are automatically included in GitHub pull request pipelines.

# Authenticate with GitHub
gh auth login --with-token <<< "$GITHUB_TOKEN"

# Collect all the context
mkdir -p .bots/context
# Collect the pull request details
gh pr view $GITHUB_HEAD_REF --json body,title,number,url,author,state,createdAt,updatedAt > .bots/context/pull-request.json
# Collect the diffs
gh pr diff $GITHUB_HEAD_REF > .bots/context/diffs.md
# TODO: include pull request comments in the context

# Combine context into a single `.bots/context.md` file
# For GitHub, we'll convert the JSON pull request details to a more readable format
echo "Pull Request Details:" > .bots/context.md
jq -r '. | to_entries[] | "\(.key): \(.value)"' .bots/context/pull-request.json >> .bots/context.md
echo -e "\n===== BEGIN FILE: .bots/context/diffs.md =====\n" >> .bots/context.md
cat .bots/context/diffs.md >> .bots/context.md

# Generate the LLM review
# TODO: move the summary to a separate multi-line variable
cat .bots/context.md | llm -m summary-model -s "Summarize this pull request. Please note any concerns in the following areas: security, performances, and best practices. For each concern, please include at least one possible solution." > .bots/summary.md

# Leave the comment
gh pr comment $GITHUB_HEAD_REF -F .bots/summary.md
