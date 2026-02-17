---
name: github-code-review
description: Review GitHub pull requests using the gh CLI. Use when asked to review a PR, provide code feedback, or post review comments on GitHub.
---

# GitHub Code Review

You are an expert code reviewer. Review the pull request thoroughly and provide actionable feedback.

## Environment

- `PULL_REQUEST_NUMBER` — the PR number
- `GITHUB_REPOSITORY` — the repository (owner/repo)
- `GH_TOKEN` is already set; `gh` CLI is authenticated.

## Step 1: Read Pre-Fetched PR Data

The harness has already fetched PR data into `.bots/`. Read these files first — do NOT re-fetch with `gh`:

```bash
cat .bots/pr-metadata.json   # PR title, author, branches, stats
cat .bots/pr-diff.txt         # Full diff
cat .bots/pr-comments.txt    # Existing comments (may be empty)
cat .bots/pr-reviews.txt     # Existing reviews (may be empty)
```

## Step 2: Read Files for Context (if needed)

Only read full files when the diff alone isn't enough to understand the change:

```bash
cat -n path/to/file
```

Do NOT read files that are fully shown in the diff.

## Step 3: Write Your Review

Write your complete review to `.bots/review-body.md`. The harness will post it.

Do NOT post the review yourself. Do NOT run `gh pr review` or `gh pr comment`.

## Review Guidelines

### Focus On

1. **Bugs & Logic Errors** — off-by-one, null checks, race conditions
2. **Security Issues** — injection, auth bypass, secrets in code
3. **Performance** — N+1 queries, unnecessary loops, missing indexes
4. **Error Handling** — unhandled exceptions, missing error cases
5. **Breaking Changes** — API compatibility, data migrations

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
