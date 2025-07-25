# Bots 🤖

This repository contains various bots that assist us in our software development process.

## Code Review 🧐💻

This is a Docker image with built-in tools and scripts for code review. It is designed to be run in a GitLab pipeline. We plan to add GitHub Action support in the future.

### GitLab Pipeline

Here is a minimal example of using the Code Review Bot in a GitLab job. It is set up to run on every merge request event, but requires a manual trigger to avoid filling up the merge request comments.

```yaml
run_code_review_bot:
  stage: bot
  image: ghcr.io/mrs-electronics-inc/bots/code-review:0.1
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

### GitHub Action

Coming soon...
