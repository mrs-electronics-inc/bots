import { issueBotHandler } from '../issue-bot';
import { Gitlab } from '@gitbeaker/rest';

// Mock fs for reading labels.json
jest.mock('fs', () => ({
  readFileSync: jest.fn(() => JSON.stringify({
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
  })),
}));

// Mock the GitLab module
jest.mock('@gitbeaker/rest');

const mockedGitlab = jest.mocked(Gitlab);

describe('issueBotHandler', () => {
  let mockApi: any;

  beforeEach(() => {
    jest.clearAllMocks();
    // Create a mock API instance
    mockApi = {
      Issues: {
        show: jest.fn(),
        edit: jest.fn(),
      },
      IssueNotes: {
        all: jest.fn().mockResolvedValue([]),
        create: jest.fn(),
        edit: jest.fn(),
      },
      ProjectLabels: {
        all: jest.fn().mockResolvedValue([
          { name: 'priority::normal' },
          { name: 'priority::high' },
          { name: 'Type::Bug' },
        ]),
      },
    };
    mockedGitlab.mockImplementation(() => mockApi as any);

    // Set up environment variables
    process.env.TOKEN_ISSUE_BOT = 'fake-token';
    process.env.PAYLOAD = JSON.stringify({
      event_type: 'issue',
      user: { name: 'TestUser' },
      object_attributes: { iid: 123 },
      project: { id: 456 },
    });
  });

  it('should add type label for valid issue title', async () => {
    mockApi.Issues.show.mockResolvedValue({
      title: 'fix: some bug',
      labels: [],
      state: 'opened',
      project_id: 456,
      iid: 123,
    });

    const result = await issueBotHandler();

    expect(result.success).toBe(true);
    expect(mockApi.Issues.edit).toHaveBeenCalledWith(456, 123, { addLabels: 'Type::Bug' });
  });

  it('should skip closed issues', async () => {
    mockApi.Issues.show.mockResolvedValue({
      title: 'fix: some bug',
      labels: [],
      state: 'closed',
      project_id: 456,
      iid: 123,
    });

    const result = await issueBotHandler();

    expect(result.success).toBe(false);
    expect(mockApi.Issues.edit).not.toHaveBeenCalled();
  });

  it('should add comment for invalid issue type', async () => {
    mockApi.Issues.show.mockResolvedValue({
      title: 'invalid: some issue',
      labels: [],
      state: 'opened',
      project_id: 456,
      iid: 123,
    });
    mockApi.IssueNotes.all.mockResolvedValue([]);

    const result = await issueBotHandler();

    expect(result.success).toBe(true);
    expect(mockApi.IssueNotes.create).toHaveBeenCalled();
  });

  it('should skip events triggered by bots', async () => {
    process.env.PAYLOAD = JSON.stringify({
      event_type: 'issue',
      user: { name: 'BotUser' },
      object_attributes: { iid: 123 },
      project: { id: 456 },
    });

    const result = await issueBotHandler();

    expect(result.success).toBe(false);
  });

  it('should return false if no token', async () => {
    delete process.env.TOKEN_ISSUE_BOT;

    const result = await issueBotHandler();

    expect(result.success).toBe(false);
  });
});