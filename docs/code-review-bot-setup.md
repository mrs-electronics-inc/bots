# Setting Up the Code Review Bot

The Code Review Bot uses [OpenCode](https://opencode.ai) with the `gh` and `glab` CLIs to provide AI-powered code reviews. It runs in CI/CD on GitHub or GitLab.

## GitHub Workflow

Here is a minimal example of using the Code Review Bot in a GitHub workflow:

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
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PULL_REQUEST_NUMBER: ${{ github.event.pull_request.number }}
        run: github_code_review.sh

      - name: Upload logs
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: bots-directory
          path: .bots/
          include-hidden-files: true
```

## GitLab Pipeline

Here is a minimal example for GitLab CI:

```yaml
code_review:
  stage: review
  image: ghcr.io/mrs-electronics-inc/bots/code-review:latest
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual
      allow_failure: true
  variables:
    OPENROUTER_API_KEY: $OPENROUTER_API_KEY
    GITLAB_TOKEN: $CODE_REVIEW_BOT_TOKEN
  script:
    - gitlab_code_review.sh
  artifacts:
    paths:
      - .bots/
    when: always
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `GH_TOKEN` | GitHub token (use `${{ secrets.GITHUB_TOKEN }}`) |
| `GITLAB_TOKEN` | GitLab personal access token with API scope |
| `PULL_REQUEST_NUMBER` | PR number (GitHub, auto-set via `${{ github.event.pull_request.number }}`) |
| `CI_MERGE_REQUEST_IID` | MR number (GitLab, auto-set in MR pipelines) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `REVIEW_MODEL` | `google/gemini-3-flash-preview` | OpenRouter model to use |

## Configuration

### Repo-Specific Instructions

Add a `.bots/instructions.md` file to your repository to provide additional context:

```markdown
- Ensure PR titles follow conventional commits format (e.g., `fix: bug description`)
- Check that CHANGELOG.md is updated
- Flag any changes to the public API
```

See [.bots/instructions.md](/.bots/instructions.md) for an example.

### Model Selection

You can override the default model via environment variable:

```yaml
env:
  REVIEW_MODEL: openai/gpt-4.1
```

Available models depend on your OpenRouter account. Popular options:
- `google/gemini-3-flash-preview` (default)
- `anthropic/claude-sonnet-4`
- `openai/gpt-4.1`

## How It Works

1. The bot uses OpenCode with a code review skill
2. The skill instructs the AI to:
   - Fetch PR/MR details using `gh` or `glab` CLI
   - Read the diff and relevant files
   - Check for repo-specific instructions
   - Post a structured review
3. Reviews focus on bugs, security issues, and significant problems
4. Style/formatting issues are left to linters
