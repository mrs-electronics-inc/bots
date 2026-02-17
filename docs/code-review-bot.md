# Code Review Bot

An automated code review bot that runs as a container in CI/CD pipelines. It uses an [OpenCode](https://opencode.ai) agent to analyze pull/merge request diffs and post review comments.

## Architecture

The bot is split into two layers:

- **Shell harness** (`github_code_review.sh` / `gitlab_code_review.sh`) — owns the full lifecycle: fetches PR metadata, runs skip logic, launches the agent, and posts the resulting comment.
- **OpenCode agent runtime** — an OpenCode session loaded with markdown skills that performs the actual review.

The agent writes its review to `.bots/review-body.md`. The harness then posts that file as a PR/MR comment. Each bot comment includes a `<!-- reviewed-sha:abc123 -->` marker so the harness can track what has already been reviewed and decide whether to skip on the next run.

Review comments include an OpenCode session-sharing link, for easy analysis of the code review.

## Setup

### GitHub Workflow

```yaml
name: Code Review Bot

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  run_code_review_bot:
    runs-on: ubuntu-latest

    container:
      image: ghcr.io/mrs-electronics-inc/bots/code-review:latest

    permissions:
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Code Review Bot
        env:
          OPENROUTER_KEY: ${{ secrets.API_KEY_CODE_REVIEW_BOT }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PULL_REQUEST_NUMBER: ${{ github.event.pull_request.number }}
        run: github_code_review.sh

      - name: Upload artifact including hidden files
        uses: actions/upload-artifact@v4
        with:
          name: bots-directory
          path: .bots/
          include-hidden-files: true
```

### GitLab Pipeline

Use the name **"Code Review Bot"** for your code review bot's token.

```yaml
run_code_review_bot:
  stage: bot
  image: ghcr.io/mrs-electronics-inc/bots/code-review:latest
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    OPENROUTER_KEY: $API_KEY_CODE_REVIEW_BOT
    GITLAB_TOKEN: $TOKEN_CODE_REVIEW_BOT
  script:
    - gitlab_code_review.sh
  artifacts:
    paths:
      - ".bots/"
```

## Skip Logic

The harness decides whether to run a full review or skip on each trigger. The rules are evaluated in order:

| Condition                                                          | Result     |
| ------------------------------------------------------------------ | ---------- |
| No prior review comment found                                      | **Review** |
| Commit message contains `[review]`                                 | **Review** |
| Previously reviewed SHA not found in history (force push / rebase) | **Review** |
| No changes since the last reviewed SHA                             | **Skip**   |
| Delta is under the line threshold (default: 20 lines)              | **Skip**   |
| Only non-code files changed (images, lock files, etc.)             | **Skip**   |
| Otherwise                                                          | **Review** |

The line threshold is configurable via the `DELTA_LINE_THRESHOLD` environment variable (see [Configuration](#configuration)).

## Configuration

| Setting                    | How to set                                | Default                | Description                                                                                 |
| -------------------------- | ----------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------- |
| Repo-specific instructions | `.bots/instructions.md` file in your repo | _(none)_               | Extra context appended to the agent's system prompt. See [example](/.bots/instructions.md). |
| Review model               | `REVIEW_MODEL` env var                    | `minimax/minimax-m2.5` | Override the LLM used for reviews.                                                          |
| Delta line threshold       | `DELTA_LINE_THRESHOLD` env var            | `20`                   | Minimum changed lines to trigger a review (below this the run is skipped).                  |

## RC Process

To test changes to the bot's Docker image before releasing:

1. Make your code changes on a feature branch.
2. Tag an RC (e.g., `v0.14.0-rc1`) and push the tag.
3. Wait for the **Publish Bot Images** workflow to build and push the image.
4. Update the workflow in your test repo to reference the new RC tag instead of `latest`.
5. Push a change to a PR and watch the run.
6. Fix any issues, tag a new RC, and repeat until satisfied.
