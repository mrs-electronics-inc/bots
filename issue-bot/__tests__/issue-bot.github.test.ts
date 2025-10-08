import { GitHubAPI } from '../apis';
import { issueBotHandler } from '../issue-bot-handler';
import { beforeEach, describe, it, expect, jest } from '@jest/globals';

// Mock fs for reading labels.json
jest.mock('fs', () => ({
  readFileSync: jest.fn(() =>
    JSON.stringify({
      fix: 'Type::Bug',
      feat: 'Type::Feature',
      chore: 'Type::Chore',
      refactor: 'Type::Refactor',
      docs: 'Type::Documentation',
      perf: 'Type::Performance',
      test: 'Type::Testing',
      debt: 'Type::Technical Debt',
      release: 'Type::Release',
      notes: 'Type::Notes',
      ci: 'Type::Continuous Integration',
    })
  ),
}));

describe('issueBotHandler - GitHub', () => {
  let mockApi: any;
  let api: GitHubAPI;

  beforeEach(() => {
    jest.clearAllMocks();
    // Create a mock API instance
    mockApi = {
      issues: {
        get: jest.fn(),
        addLabels: jest.fn(),
        createComment: jest.fn(),
        updateComment: jest.fn(),
        listComments: jest.fn(),
        listLabelsForRepo: jest.fn(),
      },
    };

    // Set up mock return values
    mockApi.issues.listComments.mockResolvedValue({ data: [] });
    mockApi.issues.listLabelsForRepo.mockResolvedValue({
      data: [{ name: 'priority::normal' }, { name: 'priority::high' }, { name: 'Type::Bug' }],
    });

    api = new GitHubAPI(mockApi);
  });

  it('should add type label for valid issue title', async () => {
    mockApi.issues.get.mockResolvedValue({
      data: {
        number: 123,
        title: 'fix: some bug',
        labels: [],
        state: 'open',
      },
    });

    const event = {
      event_type: 'issues',
      user: { name: 'TestUser' },
      object_attributes: { iid: 123 },
      repository: { full_name: 'owner/repo' },
    };

    const result = await issueBotHandler(api, event);

    expect(result.success).toBe(true);
    expect(mockApi.issues.addLabels).toHaveBeenCalledWith({
      owner: 'owner',
      repo: 'repo',
      issue_number: 123,
      labels: ['Type::Bug'],
    });
  });

  it('should skip closed issues', async () => {
    mockApi.issues.get.mockResolvedValue({
      data: {
        number: 123,
        title: 'fix: some bug',
        labels: [],
        state: 'closed',
      },
    });

    const event = {
      event_type: 'issues',
      user: { name: 'TestUser' },
      object_attributes: { iid: 123 },
      repository: { full_name: 'owner/repo' },
    };

    const result = await issueBotHandler(api, event);

    expect(result.success).toBe(false);
    expect(mockApi.issues.addLabels).not.toHaveBeenCalled();
  });

  it('should add comment for invalid issue type', async () => {
    mockApi.issues.get.mockResolvedValue({
      data: {
        number: 123,
        title: 'invalid: some issue',
        labels: [],
        state: 'open',
      },
    });
    mockApi.issues.listComments.mockResolvedValue({ data: [] });

    const event = {
      event_type: 'issues',
      user: { name: 'TestUser' },
      object_attributes: { iid: 123 },
      repository: { full_name: 'owner/repo' },
    };

    const result = await issueBotHandler(api, event);

    expect(result.success).toBe(true);
    expect(mockApi.issues.createComment).toHaveBeenCalled();
  });

  it('should skip events triggered by bots', async () => {
    const event = {
      event_type: 'issues',
      user: { name: 'BotUser' },
      object_attributes: { iid: 123 },
      repository: { full_name: 'owner/repo' },
    };

    const result = await issueBotHandler(api, event);

    expect(result.success).toBe(false);
  });
});
