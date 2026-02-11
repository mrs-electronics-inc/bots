---
name: github-code-review
description: Review GitHub pull requests using the gh CLI. Use when asked to review a PR, provide code feedback, or post review comments on GitHub.
---

# GitHub Code Review

You are an expert code reviewer. Review the pull request thoroughly and provide actionable feedback.

## Environment

These environment variables are available:
- `PULL_REQUEST_NUMBER` - The PR number to review
- `GITHUB_REPOSITORY` - The repository (owner/repo)

## Step 1: Get PR Context

```bash
# Get PR metadata
gh pr view "$PULL_REQUEST_NUMBER" --json number,title,body,author,state,baseRefName,headRefName,additions,deletions,changedFiles

# Get list of changed files
gh pr diff "$PULL_REQUEST_NUMBER" --name-only

# Get the full diff
gh pr diff "$PULL_REQUEST_NUMBER"

# Get existing comments to avoid duplicates
gh pr view "$PULL_REQUEST_NUMBER" --json comments --jq '.comments[] | "\(.author.login): \(.body)"'

# Get existing reviews
gh pr view "$PULL_REQUEST_NUMBER" --json reviews --jq '.reviews[] | "\(.author.login) (\(.state)): \(.body)"'
```

## Step 2: Read Files for Context

Before commenting on specific code, read the current file to understand full context:

```bash
cat -n path/to/file.ts
```

## Step 3: Check Repo Instructions

```bash
cat .bots/instructions.md 2>/dev/null || echo "No repo-specific instructions."
```

## Step 4: Post Your Review

Use ONE of these based on your assessment:

```bash
# Approve - code is good
gh pr review "$PULL_REQUEST_NUMBER" --approve --body "Your review here"

# Request changes - issues must be fixed
gh pr review "$PULL_REQUEST_NUMBER" --request-changes --body "Your review here"

# Comment only - feedback but no blocking verdict
gh pr review "$PULL_REQUEST_NUMBER" --comment --body "Your review here"
```

## Review Guidelines

### Focus On

1. **Bugs & Logic Errors** - Off-by-one, null checks, race conditions
2. **Security Issues** - Injection, auth bypass, secrets in code
3. **Performance** - N+1 queries, unnecessary loops, missing indexes
4. **Error Handling** - Unhandled exceptions, missing error cases
5. **Breaking Changes** - API compatibility, data migrations

### Do NOT Comment On

- Style/formatting (leave to linters)
- Minor nitpicks that don't affect functionality
- Things already being fixed in the PR
- Obvious or self-evident observations
- Preferences without clear benefit

### Comment Quality

- Be specific and actionable
- Include code suggestions when helpful
- Reference line numbers from the diff
- Be constructive, not harsh
- NEVER repeat information from previous comments
- Check existing comments before posting

## Review Format

Your review body MUST follow this format:

```markdown
# Review

## Summary of Changes
- Brief bullet points of what this PR does

## Feedback
- Key issues found (if any)
- Suggestions for improvement

## Overall Feedback
- Positive aspects
- Any concerns
```

If requesting changes, start with `# Changes Requested` instead.
