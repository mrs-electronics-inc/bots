---
name: gitlab-code-review
description: Review GitLab merge requests using the glab CLI. Use when asked to review an MR, provide code feedback, or post review comments on GitLab.
---

# GitLab Code Review

You are an expert code reviewer. Review the merge request thoroughly and provide actionable feedback.

## Environment

These environment variables are available:
- `CI_MERGE_REQUEST_IID` - The MR number to review
- `CI_PROJECT_PATH` - The project path
- `CI_MERGE_REQUEST_TITLE` - MR title
- `CI_MERGE_REQUEST_DESCRIPTION` - MR description

## Step 1: Get MR Context

```bash
# Get MR metadata
glab mr view "$CI_MERGE_REQUEST_IID"

# Get list of changed files
glab mr diff "$CI_MERGE_REQUEST_IID" --name-only 2>/dev/null || glab mr diff "$CI_MERGE_REQUEST_IID" | grep -E '^diff --git' | sed 's/diff --git a\///' | sed 's/ b\/.*//'

# Get the full diff
glab mr diff "$CI_MERGE_REQUEST_IID"

# Get existing notes/comments to avoid duplicates
glab mr view "$CI_MERGE_REQUEST_IID" --comments
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

```bash
# Post your review as a note
glab mr note "$CI_MERGE_REQUEST_IID" --message "Your review here"

# If the MR is good, approve it
glab mr approve "$CI_MERGE_REQUEST_IID"
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
