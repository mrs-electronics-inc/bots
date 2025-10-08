# Issue Bot

A TypeScript-based bot that automatically manages issue labels and comments for GitLab and GitHub repositories.

## Features

- **Multi-platform**: Supports both GitLab and GitHub
- **Type-based labeling**: Automatically adds labels based on issue title prefixes (fix, feat, chore, etc.)
- **Priority management**: Ensures issues have appropriate priority labels
- **Comment handling**: Adds helpful comments for invalid issue formats
- **Bot detection**: Prevents infinite loops by ignoring bot-triggered events

## Setup

### Configuration

Labels are configured in `.bots/labels.json`:

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
  "ci": "Type::Continuous Integration"
}
```

### Usage

#### GitLab

```typescript
import { GitLabAPI, issueBotHandler } from './issue-bot';

const api = new GitLabAPI(gitlabInstance);
const event = { /* GitLab webhook payload */ };
await issueBotHandler(api, event);
```

#### GitHub

```typescript
import { GitHubAPI, issueBotHandler } from './issue-bot';

const api = new GitHubAPI(octokitInstance);
const event = { /* GitHub webhook payload */ };
await issueBotHandler(api, event);
```
