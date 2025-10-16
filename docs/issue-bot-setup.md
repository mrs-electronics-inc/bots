# Setting Up the Issue Bot

This page shows examples of how to set up the Issue Bot in Gitlab CI/CD and configure its operation.

## Configuration

Define the type labels for the bot to apply to issues by including a `.bots/labels.json` file in your repository.

An example file might look like this:

```json
{
  "fix": "Type::Bug",
  "feat": "Type::Feature",
  "chore": "Type::Chore",
  "refactor": "Type::Refactor",
  "docs": "Type::Documentation",
  "perf": "Type::Performance",
  "test": "Type::Testing",
  "debt": "Type::Technical Debt",
  "release": "Type::Release",
  "notes": "Type::Notes",
  "ci": "Type::CI/CD"
}
```

## GitLab Pipeline

### Webhook Setup

<!-- TODO(#46): add webhook setup -->

### Pipeline Job Setup

Here is a minimal example of using the Issue Bot in a GitLab job. It is set up to run when triggered by the webhook you just created.

Be sure to use the name "Issue Bot" for your issue bot's token.

```yaml
run_issue_bot:
  stage: bot
  image: ghcr.io/mrs-electronics-inc/bots/issue:latest
  rules:
    - if: $CI_PIPELINE_SOURCE == "trigger"
  variables:
    GITLAB_TOKEN: $TOKEN_ISSUE_BOT
  script:
    - export PAYLOAD=$(cat $TRIGGER_PAYLOAD)
    - npx tsx /bin/issue-bot-handler.ts
```
