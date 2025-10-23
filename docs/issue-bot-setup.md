# Setting Up the Issue Bot

This page shows examples of how to set up the Issue Bot in GitLab CI/CD and configure its operation.

## GitHub Workflow

Coming soon...

## GitLab Pipeline

### Token and Webhook Setup

To run the issue bot, you will first need to set up an access token so that it's able to access your GitLab projects. Create the token at the group level so that only one token is needed.

1. Go to **Settings > Access tokens** in your group.
2. Click on **Add new token**.
3. Name the token whatever you want. "Issue Bot" is fine.
4. Use the `Developer` role for the token, and give it `api` and `read_api` permissions only.
5. Click **Create group access token** to create the token. Make sure you copy the token's value before you leave the page!
6. Next, go to **Settings > CI/CD**, and expand the **Variables** section.
7. Click on **Add variable**.
8. Set the visibility to `Masked`. Enable variable protection. Disable variable expansion.
9. Paste the copied access token into the variable.
10. Click **Add variable** at the bottom to save it.

Now that you have the access token set up and have made it accessible in CI/CD jobs, you can set up the webhook. This webhook will trigger pipelines whenever certain events occur in the project.

Note that webhooks have to be created at the project/repo level, not the group level.

1. Go to **Settings > CI/CD** and open the **Pipeline trigger tokens** section.
2. Create a new token. Name it "Issue Bot". Set it to never expire. Click **Create pipeline trigger token** to save it.
3. Copy the value of the new token. We will need it for the webhook.
4. Now, go to **Settings > Webhooks**.
5. Click on **Add new webhook**. Name it "Issue Bot".
6. Set the URL using this format: `https://gitlab.com/api/v4/projects/<project-id>/ref/<branch>/trigger/pipeline?token=<trigger-token>`
    - `project-id` can be found in **Settings > General**. It is the unique ID for your GitLab project.
    - `branch` should be whatever branch you want pipelines to run on. Typically this will be your default branch.
    - `trigger-token` is the pipeline trigger token you just created.
7. Set the triggers for the webhook. For this issue bot you will just need `Issue events`.
8. Make sure SSL verification is enabled, then click **Add webhook** to finish.

You've now created the webhook for triggering the issue bot! All that's left is to actually run the bot from a CI/CD job, as shown in the next section.

The basic flow is:

- Create GitLab access token for the bot scripts to use when running in CI/CD jobs
- Create pipeline trigger token and webhook to trigger pipelines on certain project events

Here are some helpful links if you want more information:

- Group access tokens: https://docs.gitlab.com/user/group/settings/group_access_tokens/#group-access-tokens
- Project access tokens: https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html#project-access-tokens
- Pipeline trigger tokens: https://docs.gitlab.com/ci/triggers/#create-a-pipeline-trigger-token
- Webhooks: https://docs.gitlab.com/ci/triggers/#use-a-webhook, https://docs.gitlab.com/user/project/integrations/webhooks/

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
    - gitlab_issue_bot.sh
```

## Configuration

Define the type labels for the bot to apply to issues by including a `.bots/labels.json` file in your repository.

An example file might look like this:

```json
{
  "typeLabels": {
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
  },
  "priorityLabels": [
    "Priority::Normal",
    "Priority::Important",
    "Priority::Must Have",
    "Priority::Hot Fix",
  ],
  "defaultPriorityLabel": "Priority::Normal",
}
```
