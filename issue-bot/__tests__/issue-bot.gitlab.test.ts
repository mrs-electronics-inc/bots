import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { GitLabAPI } from '../src/apis';
import { issueBotHandler } from '../src/issue-bot-backend';

// Mock fs for reading config file
jest.mock('fs', () => ({
  readFileSync: jest.fn(() =>
    JSON.stringify({
      typeLabels: {
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
        ci: 'Type::CI/CD',
      },
      priorityLabels: [
        'Priority::Normal',
        'Priority::Important',
        'Priority::Must Have',
        'Priority::Hot Fix',
      ],
      defaultPriorityLabel: 'Priority::Normal',
    })
  ),
  existsSync: jest.fn(() => true),
}));

describe('issue bot', () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let mockApi: any;
  let api: GitLabAPI;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let fakeEvent: any;

  beforeEach(() => {
    jest.clearAllMocks();
    // Create a mock API instance
    mockApi = {
      Issues: {
        show: jest.fn(),
        edit: jest.fn(),
      },
      IssueNotes: {
        all: jest.fn(),
        create: jest.fn(),
        edit: jest.fn(),
      },
      ProjectLabels: {
        all: jest.fn(),
      },
    };

    // Set up mock return values
    mockApi.IssueNotes.all.mockResolvedValue([]);
    mockApi.ProjectLabels.all.mockResolvedValue([
      { name: 'priority::normal' },
      { name: 'priority::high' },
      { name: 'Type::Bug' },
    ]);

    api = new GitLabAPI(mockApi);

    fakeEvent = {
      event_type: 'issue',
      user: { name: 'TestUser' },
      object_attributes: { iid: 123 },
      project: { id: 456 },
      repository: { name: 'issue-bot-test' },
    };
  });

  it('should skip events triggered by bots', async () => {
    fakeEvent.user.name = 'Fake Issue Bot';

    const result = await issueBotHandler(api, fakeEvent, { silent: true });

    expect(result.success).toBe(false);
  });

  it('should add type label for valid issue title', async () => {
    mockApi.Issues.show.mockResolvedValue({
      iid: 123,
      title: 'fix: some bug',
      labels: [],
      state: 'opened',
      project_id: 456,
    });

    const result = await issueBotHandler(api, fakeEvent, { silent: true });

    expect(result.success).toBe(true);
    expect(mockApi.Issues.edit).toHaveBeenCalledWith(456, 123, { addLabels: 'Type::Bug' });
  });

  it('should skip closed issues', async () => {
    mockApi.Issues.show.mockResolvedValue({
      iid: 123,
      title: 'fix: some bug',
      labels: [],
      state: 'closed',
      project_id: 456,
    });

    const result = await issueBotHandler(api, fakeEvent, { silent: true });

    expect(result.success).toBe(false);
    expect(mockApi.Issues.edit).not.toHaveBeenCalled();
    expect(mockApi.IssueNotes.create).not.toHaveBeenCalled();
  });

  it('should add comment for invalid issue type', async () => {
    mockApi.Issues.show.mockResolvedValue({
      iid: 123,
      title: 'invalid: some issue',
      labels: [],
      state: 'opened',
      project_id: 456,
    });
    mockApi.IssueNotes.all.mockResolvedValue([]);

    const result = await issueBotHandler(api, fakeEvent, { silent: true });

    expect(result.success).toBe(true);
    expect(mockApi.IssueNotes.create).toHaveBeenCalled();
  });
});
