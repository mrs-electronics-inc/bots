import { Gitlab, IssueSchema, SimpleLabelSchema } from '@gitbeaker/rest';

type GitlabInstance = InstanceType<typeof Gitlab>;

// This defines an interface for the components of an issue that we care about.
export interface Issue {
  // On GitLab, this will be issue.iid, not issue.id.
  id: number;
  title: string;
  labels: Label[];
  state: 'open' | 'closed';
  projectId: string | number;
}

export interface Label {
  name: string;
}

export interface Comment {
  id: number;
  body: string;
  author: { name: string };
}

// This is the type of the object that will be included in the job payload.
export enum IssueEventType {
  issue,
  comment,
}
export interface IssueEvent {
  eventType: IssueEventType;
  user: { name: string };
  issue: { id: number };
  project: { id: number };
  repository: { name: string };
}

// These are all of the methods that the issue bot will need to use.
// These are platform-agnostic, which means that the same methods will be used on both GitHub and GitLab.
export interface IssueBotAPI {
  parseIssueEvent(eventBody: unknown): IssueEvent | undefined;
  getIssue(projectId: string | number, issueId: number): Promise<Issue>;
  editIssue(
    projectId: string | number,
    issueId: number,
    options: { addLabel: Label }
  ): Promise<void>;
  getLabels(projectId: string | number): Promise<Label[]>;
  createComment(projectId: string | number, issueId: number, body: string): Promise<void>;
  editComment(
    projectId: string | number,
    issueId: number,
    commentId: number,
    newBody: string
  ): Promise<void>;
  getComments(projectId: string | number, issueId: number): Promise<Comment[]>;
}

// ---------------------------------------------------------------------------------------------
// GitLab API implementation
// ---------------------------------------------------------------------------------------------

// This interface defines all the important parts of the GitLab event.
export interface GitlabIssueEventBody {
  event_type: string;
  object_attributes: {
    noteable_type?: string;
    iid?: number;
  };
  issue?: {
    iid: number;
  };
  user: {
    name: string;
  };
  project: {
    id: number;
  };
  repository: {
    name: string;
  };
}

function isGitlabIssueEventBody(body: unknown): body is GitlabIssueEventBody {
  return (
    typeof body === 'object' &&
    body !== null &&
    'event_type' in body &&
    'user' in body &&
    'project' in body &&
    'repository' in body
  );
}

export class IssueBotGitlabAPI implements IssueBotAPI {
  constructor(private api: GitlabInstance) {}

  parseIssueEvent(eventBody: GitlabIssueEventBody): IssueEvent | undefined {
    // Return early with undefined if the payload does not match what we're expecting.
    if (!isGitlabIssueEventBody(eventBody)) {
      return undefined;
    }

    let eventType: IssueEventType;
    if (eventBody!.event_type == 'issue') {
      eventType = IssueEventType.issue;
    } else if (
      eventBody!.event_type == 'note' &&
      eventBody.object_attributes.noteable_type == 'Issue'
    ) {
      eventType = IssueEventType.comment;
    } else {
      // If we can't figure what type the event is then don't continue trying to parse it.
      // Doing so could cause errors, and it's clearly not an event we care about.
      return undefined;
    }

    // Make sure we can determine a valid issue ID.
    const issueId =
      (eventType == IssueEventType.issue
        ? eventBody.object_attributes.iid
        : eventBody.issue?.iid) ?? -1;
    if (issueId < 0) {
      return undefined;
    }

    return {
      eventType,
      user: {
        name: eventBody.user.name,
      },
      issue: {
        id: issueId,
      },
      project: {
        id: eventBody.project.id,
      },
      repository: {
        name: eventBody.repository.name,
      },
    };
  }

  async getIssue(projectId: number, issueId: number): Promise<Issue> {
    const issue = (await this.api.Issues.show(issueId, { projectId })) as IssueSchema;

    // Figure out whether the labels were returned as objects or strings and parse out accordingly.
    var labels: Label[] = [];
    const labelsAsStrings = issue.labels as string[];
    const labelsAsSchema = issue.labels as SimpleLabelSchema[];
    if (issue.labels.length > 0) {
      if (typeof issue.labels[0] === 'string') {
        labels = labelsAsStrings.map((l) => ({ name: l }));
      } else {
        labels = labelsAsSchema.map((l) => ({ name: l.name }));
      }
    }

    return {
      id: issue.iid,
      title: issue.title,
      labels,
      state: issue.state === 'opened' ? 'open' : 'closed',
      projectId: issue.project_id as number,
    };
  }

  async editIssue(projectId: number, issueId: number, options: { addLabel: Label }): Promise<void> {
    if (options.addLabel) {
      await this.api.Issues.edit(projectId, issueId, { addLabels: options.addLabel.name });
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
