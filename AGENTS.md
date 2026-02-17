# Agent Guidance

## Repo Structure

- `code-review-bot/` — Docker image that runs AI-powered code reviews on PRs/MRs
- `issue-bot/` — Docker image for issue triage (GitLab only)
- `docs/` — Setup guides for each bot

## Code Review Bot Architecture

The code-review-bot uses [OpenCode](https://opencode.ai) as the AI agent runtime with markdown skills.

- **Shell harness** (`github_code_review.sh`, `gitlab_code_review.sh`) — owns the entire lifecycle: pre-fetches data, decides whether to skip, launches the agent, posts/updates the comment
- **Skills** (`skills/*/SKILL.md`) — markdown instructions that tell the agent how to review. The agent reads pre-fetched files and writes its review to `.bots/review-body.md`. It does NOT post comments itself.
- **Skip logic** (`should_review.sh`) — shared script that determines if a review is needed based on delta analysis since the last reviewed commit
- **Comment lifecycle** — the harness creates or updates a single bot comment, embedding `<!-- reviewed-sha:... -->` to track what was reviewed

## Changelog

- Update `CHANGELOG.md` with each PR. One line per PR, no sub-bullets.
- Format: `- [#N](url) - description`

## Git Rules

- Never force push. If a commit is already pushed, make a new commit instead of amending.
- Use conventional commit format for commit messages (e.g., `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `perf:`, `refactor:`).

## RC Process for Docker Image Changes

When working on changes to Docker-based bots (e.g., code-review-bot):

1. Make code changes on the feature branch and commit
2. Tag an RC (e.g., `v0.14.0-rc1`) and push the tag
3. Wait for the Publish Bot Images workflow to complete
4. Update the workflow that references the image to the new tag
5. Push the workflow change to trigger a test run
6. Watch the run, download artifacts, analyze output
7. Fix issues and repeat from step 1

Never push the workflow bump until the image is built.
