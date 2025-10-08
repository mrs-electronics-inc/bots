import { Gitlab } from '@gitbeaker/rest';
import { Octokit } from '@octokit/rest';

type GitlabInstance = InstanceType<typeof Gitlab>;
type OctokitInstance = InstanceType<typeof Octokit>;

export interface IssueBotAPI {
  getIssue(projectId: string | number, issueId: number): Promise<Issue>;
  editIssue(projectId: string | number, issueId: number, options: { addLabels?: string[] }): Promise<void>;
  getLabels(projectId: string | number): Promise<Label[]>;
  createComment(projectId: string | number, issueId: number, comment: string): Promise<void>;
  editComment(projectId: string | number, issueId: number, commentId: number, comment: string): Promise<void>;
  getComments(projectId: string | number, issueId: number): Promise<Comment[]>;
}

// Common interfaces
export interface Issue {
  iid: number;
  title: string;
  labels: string[];
  state: 'opened' | 'closed';
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
      state: issue.state === 'opened' ? 'opened' : 'closed',
      project_id: issue.project_id as number,
    };
  }

  async editIssue(projectId: number, issueId: number, options: { addLabels?: string[] }): Promise<void> {
    if (options.addLabels) {
      await this.api.Issues.edit(projectId, issueId, { addLabels: options.addLabels[0] });
    }
  }

  async getLabels(projectId: number): Promise<Label[]> {
    const labels = await this.api.ProjectLabels.all(projectId);
    return labels.map(l => ({ name: l.name }));
  }

  async createComment(projectId: number, issueId: number, comment: string): Promise<void> {
    await this.api.IssueNotes.create(projectId, issueId, comment);
  }

  async editComment(projectId: number, issueId: number, commentId: number, comment: string): Promise<void> {
    await this.api.IssueNotes.edit(projectId, issueId, commentId, { body: comment });
  }

  async getComments(projectId: number, issueId: number): Promise<Comment[]> {
    const notes = await this.api.IssueNotes.all(projectId, issueId);
    return notes.map(n => ({
      id: n.id,
      body: n.body,
      author: { name: n.author.name },
    }));
  }
}

// GitHub API implementation
export class GitHubAPI implements IssueBotAPI {
  constructor(private api: OctokitInstance) {}

  async getIssue(repo: string, issueId: number): Promise<Issue> {
    const { data } = await this.api.issues.get({ owner: repo.split('/')[0], repo: repo.split('/')[1], issue_number: issueId });
    return {
      iid: data.number,
      title: data.title,
      labels: data.labels.map((l: any) => typeof l === 'string' ? l : l.name),
      state: data.state === 'open' ? 'opened' : 'closed',
      repository: repo,
    };
  }

  async editIssue(repo: string, issueId: number, options: { addLabels?: string[] }): Promise<void> {
    if (options.addLabels) {
      await this.api.issues.addLabels({
        owner: repo.split('/')[0],
        repo: repo.split('/')[1],
        issue_number: issueId,
        labels: options.addLabels,
      });
    }
  }

  async getLabels(repo: string): Promise<Label[]> {
    const { data } = await this.api.issues.listLabelsForRepo({ owner: repo.split('/')[0], repo: repo.split('/')[1] });
    return data.map(l => ({ name: l.name }));
  }

  async createComment(repo: string, issueId: number, comment: string): Promise<void> {
    await this.api.issues.createComment({
      owner: repo.split('/')[0],
      repo: repo.split('/')[1],
      issue_number: issueId,
      body: comment,
    });
  }

  async editComment(repo: string, issueId: number, commentId: number, comment: string): Promise<void> {
    await this.api.issues.updateComment({
      owner: repo.split('/')[0],
      repo: repo.split('/')[1],
      comment_id: commentId,
      body: comment,
    });
  }

  async getComments(repo: string, issueId: number): Promise<Comment[]> {
    const { data } = await this.api.issues.listComments({
      owner: repo.split('/')[0],
      repo: repo.split('/')[1],
      issue_number: issueId,
    });
    return data.map(c => ({
      id: c.id,
      body: c.body || '',
      author: { name: c.user?.login || '' },
    }));
  }
}