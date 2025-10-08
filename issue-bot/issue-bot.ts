import { Gitlab, IssueSchema, LabelSchema } from '@gitbeaker/rest';
import fs from 'fs';

type GitlabInstance = InstanceType<typeof Gitlab>;

const labelsPath = '.bots/labels.json';
const labelsData = JSON.parse(fs.readFileSync(labelsPath, 'utf8'));
const TYPE_LABELS: Record<string, string> = labelsData;

const VALID_TYPES = Object.keys(TYPE_LABELS);

type IssueType = typeof VALID_TYPES[number];

interface GitLabPayload {
    event_type: string;
    user: {
        name: string;
    };
    object_attributes?: {
        iid: number;
        noteable_type?: string;
    };
    issue?: {
        iid: number;
    };
    project: {
        id: number;
    };
}



const extractIssueType = (issueTitle: string): IssueType | null => {
    const match = issueTitle.match(/^(\w+)(?:\(.*?\))?:/);

    if (match) {
        const type = match[1];
        return VALID_TYPES.includes(type) ? type as IssueType : null;
    }

    return null;
};

export const issueBotHandler = async (): Promise<{ success: boolean; timestamp?: number }> => {
    console.log('I am the issue bot!');
    const token = process.env.TOKEN_ISSUE_BOT;
    if (!token) {
        console.error('No gitlab token supplied!');
        return { success: false };
    }

    const payload: GitLabPayload = JSON.parse(process.env.PAYLOAD!);
    console.log('Payload:', payload);

    if (payload.user.name.includes('Bot')) {
        console.log('Leaving early, this handler was triggered by a bot.');
        // Prevent trigger loop.
        return { success: false };
    }

    const isIssueEvent = payload.event_type === 'issue';
    const isIssueNoteEvent =
        payload.event_type === 'note' &&
        payload.object_attributes?.noteable_type === 'Issue';

    if (!(isIssueEvent || isIssueNoteEvent)) {
        console.log('Ignoring this event');
        return { success: false };
    }
    const issueIid = isIssueEvent
        ? payload.object_attributes!.iid
        : payload.issue!.iid;
    console.log('project id:', payload.project.id, 'issue iid:', issueIid);

    const api = new Gitlab({ token });
    const issue = await api.Issues.show(issueIid, {
        projectId: payload.project.id,
    });

    if (issue.state === 'closed') {
        console.log('Leaving early, this issue is closed.');
        return { success: false };
    }

    const type = extractIssueType(issue.title);
    if (type == null) {
        console.error('issue must have a valid type');
        let comment =
            'The issue title must begin with one of the following prefixes:\n';
        for (const type of VALID_TYPES) {
            comment += `   - ${type}\n`;
        }
        comment +=
            '\n\nPlease see [this page](https://gitlab.com/mrs-electronics/spoke-zone/sz/-/blob/develop/apps/wiki/process/issues/labels/Type.md) for more information.';
        await addBotComment(api, payload.project.id, issueIid, comment);
    } else {
        console.log('issue type:', type);
        const label = TYPE_LABELS[type];
        if (!(issue.labels as string[]).includes(label)) {
            await api.Issues.edit(payload.project.id, issueIid, {
                addLabels: label,
            });
        }
    }

    // Make sure the issue has a priority label. Add the default priority label if needed.
    await checkHasRequiredLabel(api, issue, 'priority', /::(normal|none)$/i);

    // TODO: apply epic label, or leave comment if epic is missing

    return { success: true, timestamp: Date.now() };
};

// Get all the scoped labels in a project with scope "scope".
// NOTE: this will automatically grab labels from all ancestor groups too.
const getScopedLabelList = async (api: GitlabInstance, projectId: number, scope: string): Promise<string[]> => {
    const allLabels = await api.ProjectLabels.all(projectId);
    return allLabels
        .map((label) => label.name)
        .filter((name): name is string =>
            name !== undefined && name.toLowerCase().includes(scope.toLowerCase() + '::'),
        );
};

const checkHasRequiredLabel = async (api: GitlabInstance, issue: IssueSchema, labelScope: string, defaultRegex: RegExp): Promise<void> => {
    // Get a list of scoped labels according to "labelScope".
    const scopedLabelList = await getScopedLabelList(
        api,
        issue.project_id,
        labelScope,
    );

    // Find the default label in scoped list according to "defaultRegex".
    const defaultScopedLabel = scopedLabelList.find((name) => {
        return name.match(defaultRegex) !== null;
    });

    // Log the list of labels and the default.
    console.log(labelScope + ' labels: ' + scopedLabelList);
    console.log('Default ' + labelScope + ' label: ' + defaultScopedLabel);

    // Determine whether the issue in question has one of the scoped labels already.
    const hasOneOfRequiredLabels = (issue.labels as string[]).some((l) =>
        scopedLabelList.includes(l),
    );

    // If it does not, then add the default. Comment on the issue explaining what happened.
    if (!hasOneOfRequiredLabels) {
        let comment = 'The issue must have one of the following labels:\n';
        for (const label of scopedLabelList) {
            comment += `   - ~"${label}"\n`;
        }
        comment += `\n\nI am assigning the default label ~"${defaultScopedLabel}". Please replace it with the correct label.`;
        await addBotComment(api, issue.project_id, issue.iid, comment);
        await api.Issues.edit(issue.project_id, issue.iid, {
            addLabels: defaultScopedLabel,
        });
    }
};

const addBotComment = async (api: GitlabInstance, projectId: number, issueIid: number, comment: string): Promise<void> => {
    const notes = await api.IssueNotes.all(projectId, issueIid);
    const botNotes = notes.filter((n: any) => n.author.name.includes('Bot'));
    if (botNotes.length > 0) {
        // Use the most recent bot note
        const botNote = botNotes[botNotes.length - 1];
        // Append the new comment
        const body = botNote.body + '\n\n---\n\n' + comment;
        await api.IssueNotes.edit(projectId, issueIid, botNote.id, { body });
    } else {
        // No existing bot comments, create a new one
        await api.IssueNotes.create(projectId, issueIid, comment);
    }
};

issueBotHandler();