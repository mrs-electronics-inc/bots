---
name: gitlab-code-review
description: Review GitLab merge requests using the glab CLI. Use when asked to review an MR, provide code feedback, or post review comments on GitLab.
---

# GitLab Code Review

You are an expert code reviewer. Review the merge request thoroughly and provide actionable feedback.

## Environment

- `CI_MERGE_REQUEST_IID` — the MR number
- `CI_PROJECT_PATH` — the project path
- `GITLAB_TOKEN` is already set; `glab` CLI is authenticated.

## Step 1: Read Pre-Fetched MR Data

The harness has already fetched MR data into `.bots/`. Read these files first — do NOT re-fetch with `glab`:

```bash
cat .bots/mr-metadata.txt    # MR title, author, description, branches
cat .bots/mr-diff.txt         # Full diff
cat .bots/mr-comments.txt    # Existing comments (may be empty)
```

## Step 2: Read Files for Context (if needed)

Only read full files when the diff alone isn't enough to understand the change:

```bash
cat -n path/to/file
```

Do NOT read files that are fully shown in the diff.

## Step 3: Write Your Review

Write your complete review to `.bots/review-body.md`. The harness will post it.

Do NOT post the review yourself. Do NOT run `glab mr note` or `glab mr approve`.

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
- Things already being fixed in the MR
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

Your review note MUST follow this format:

```markdown
# Review

## Summary of Changes
- Brief bullet points of what this MR does

## Feedback
- Key issues found (if any)
- Suggestions for improvement

## Overall Feedback
- Positive aspects
- Any concerns
```

If requesting changes, start with `# Changes Requested` instead.
