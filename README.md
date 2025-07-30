# Bots 🤖

This repository contains various bots that assist us in our software development process.

## Code Review 🧐💻

This is a Docker image with built-in tools and scripts for code review. It is designed to be run in CI/CD in either GitHub or GitLab.

### Set Up

#### GitHub Workflow

Here is a minimal example of using the Code Review Bot in a GitHub workflow. It is set up to run on every pull request event.

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
      volumes:
        - ${{ github.workspace }}:/repo
    defaults:
      run:
        working-directory: /repo
    permissions:
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Run Code Review Bot
        env:
          OPENROUTER_KEY: ${{ secrets.API_KEY_CODE_REVIEW_BOT }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: github_code_review.sh
```

#### GitLab Pipeline

Here is a minimal example of using the Code Review Bot in a GitLab job. It is set up to run on every merge request event, but requires a manual trigger to avoid filling up the merge request comments.

```yaml
run_code_review_bot:
  stage: bot
  image: ghcr.io/mrs-electronics-inc/bots/code-review:latest
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: manual
      allow_failure: true # Necessary so that Gitlab doesn't block the pipeline
  variables:
     OPENROUTER_KEY: $API_KEY_CODE_REVIEW_BOT
     GITLAB_TOKEN: $TOKEN_CODE_REVIEW_BOT
  script:
    # Run the built-in script for GitLab code review
    - gitlab_code_review.sh
```

### Configuration

You can add additional instructions to the bot's system prompt by including a `.bots/instructions.md` file in your repository.

See an example [here](/.bots/instructions.md).
