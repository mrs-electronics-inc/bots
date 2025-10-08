# Setting Up the Code Review Bot

This page shows examples of how to set up the Code Review Bot in GitHub and Gitlab CI/CD, along with steps for optional extra configuration.

## GitHub Workflow

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
          PULL_REQUEST_NUMBER: ${{ github.event.pull_request.number }}
        run: github_code_review.sh

      - name: Upload artifact including hidden files
        uses: actions/upload-artifact@v4
        with:
          name: bots-directory
          path: .bots/
          include-hidden-files: true
```

## GitLab Pipeline

Here is a minimal example of using the Code Review Bot in a GitLab job. It is set up to run on every merge request event, but requires a manual trigger to avoid filling up the merge request comments.

Be sure to use the name "Code Review Bot" for your code review bot's token.

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
  artifacts:
    paths:
      - ".bots/"
```

## Configuration

You can add additional instructions to the bot's system prompt by including a `.bots/instructions.md` file in your repository.

See an example [here](/.bots/instructions.md).
