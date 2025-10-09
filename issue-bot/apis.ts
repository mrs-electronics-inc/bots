import { Gitlab } from '@gitbeaker/rest';

type GitlabInstance = InstanceType<typeof Gitlab>;

export interface IssueBotAPI {
  getIssue(projectId: string | number, issueId: number): Promise<Issue>;
  editIssue(
    projectId: string | number,
    issueId: number,
    options: { addLabels?: string[] }
  ): Promise<void>;
  getLabels(projectId: string | number): Promise<Label[]>;
  createComment(projectId: string | number, issueId: number, comment: string): Promise<void>;
  editComment(
    projectId: string | number,
    issueId: number,
    commentId: number,
    comment: string
  ): Promise<void>;
  getComments(projectId: string | number, issueId: number): Promise<Comment[]>;
}

// Common interfaces
export interface Issue {
  iid: number;
  title: string;
  labels: string[];
  state: 'open' | 'closed';
  project_id?: number;
  repository?: string;
}

interface Label {
  name: string;
}

interface Comment {
  id: number;
  body: string;
  author: { name: string };
}

// GitLab API implementation
export class GitLabAPI implements IssueBotAPI {
  constructor(private api: GitlabInstance) {}

  async getIssue(projectId: number, issueId: number): Promise<Issue> {
    const issue = await this.api.Issues.show(issueId, { projectId });
    return {
      iid: issue.iid,
      title: issue.title,
      labels: issue.labels as string[],
      state: issue.state === 'opened' ? 'open' : 'closed',
      project_id: issue.project_id as number,
    };
  }

  async editIssue(
    projectId: number,
    issueId: number,
    options: { addLabels?: string[] }
  ): Promise<void> {
    if (options.addLabels) {
      await this.api.Issues.edit(projectId, issueId, { addLabels: options.addLabels[0] });
    }
  }

  async getLabels(projectId: number): Promise<Label[]> {
    const labels = await this.api.ProjectLabels.all(projectId);
    return labels.map((l) => ({ name: l.name }));
  }

  async createComment(projectId: number, issueId: number, comment: string): Promise<void> {
    await this.api.IssueNotes.create(projectId, issueId, comment);
  }

  async editComment(
    projectId: number,
    issueId: number,
    commentId: number,
    comment: string
  ): Promise<void> {
    await this.api.IssueNotes.edit(projectId, issueId, commentId, { body: comment });
  }

  async getComments(projectId: number, issueId: number): Promise<Comment[]> {
    const notes = await this.api.IssueNotes.all(projectId, issueId);
    return notes.map((n) => ({
      id: n.id,
      body: n.body,
      author: { name: n.author.name },
    }));
  }
}
