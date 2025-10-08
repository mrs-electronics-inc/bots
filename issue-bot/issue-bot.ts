import { IssueBotAPI, Issue } from './apis';
import fs from 'fs';

const labelsPath = '.bots/labels.json';
const labelsData = JSON.parse(fs.readFileSync(labelsPath, 'utf8'));
const TYPE_LABELS: Record<string, string> = labelsData;

const VALID_TYPES = Object.keys(TYPE_LABELS);

type IssueType = typeof VALID_TYPES[number];

interface IssueEvent {
  event_type: string;
  user: { name: string };
  object_attributes?: { iid: number };
  issue?: { iid: number };
  project?: { id: number };
  repository?: { full_name: string };
}

const extractIssueType = (issueTitle: string): IssueType | null => {
    const match = issueTitle.match(/^(\w+)(?:\(.*?\))?:/);

    if (match) {
        const type = match[1];
        return VALID_TYPES.includes(type) ? type as IssueType : null;
    }

    return null;
};

export const issueBotHandler = async (api: IssueBotAPI, event: IssueEvent): Promise<{ success: boolean; timestamp?: number }> => {
    console.log('I am the issue bot!');
    console.log('Event:', event);

    if (event.user.name.includes('Bot')) {
        console.log('Leaving early, this handler was triggered by a bot.');
        // Prevent trigger loop.
        return { success: false };
    }

    const isIssueEvent = event.event_type === 'issue' || event.event_type === 'issues';
    const isIssueNoteEvent =
        event.event_type === 'note' ||
        event.event_type === 'issue_comment';

    if (!(isIssueEvent || isIssueNoteEvent)) {
        console.log('Ignoring this event');
        return { success: false };
    }
    const projectId = event.project?.id || event.repository?.full_name || 0;
    const issueIid = event.object_attributes?.iid || event.issue?.iid || 0;
    console.log('project/repo:', projectId, 'issue iid:', issueIid);

    const issue = await api.getIssue(projectId, issueIid);

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
        await addBotComment(api, projectId, issueIid, comment);
    } else {
        console.log('issue type:', type);
        const label = TYPE_LABELS[type];
        if (!issue.labels.includes(label)) {
            await api.editIssue(projectId, issueIid, { addLabels: [label] });
        }
    }

    // Make sure the issue has a priority label. Add the default priority label if needed.
    await checkHasRequiredLabel(api, issue, projectId, 'priority', /::(normal|none)$/i);

    // TODO: apply epic label, or leave comment if epic is missing

    return { success: true, timestamp: Date.now() };
};

// Get all the scoped labels in a project/repo with scope "scope".
const getScopedLabelList = async (api: IssueBotAPI, projectId: string | number, scope: string): Promise<string[]> => {
    const allLabels = await api.getLabels(projectId);
    return allLabels
        .map((label) => label.name)
        .filter((name) =>
            name.toLowerCase().includes(scope.toLowerCase() + '::'),
        );
};

const checkHasRequiredLabel = async (api: IssueBotAPI, issue: Issue, projectId: string | number, labelScope: string, defaultRegex: RegExp): Promise<void> => {
    // Get a list of scoped labels according to "labelScope".
    const scopedLabelList = await getScopedLabelList(
        api,
        projectId,
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
    const hasOneOfRequiredLabels = issue.labels.some((l) =>
        scopedLabelList.includes(l),
    );

    // If it does not, then add the default. Comment on the issue explaining what happened.
    if (!hasOneOfRequiredLabels && defaultScopedLabel) {
        let comment = 'The issue must have one of the following labels:\n';
        for (const label of scopedLabelList) {
            comment += `   - ~"${label}"\n`;
        }
        comment += `\n\nI am assigning the default label ~"${defaultScopedLabel}". Please replace it with the correct label.`;
        await addBotComment(api, projectId, issue.iid, comment);
        await api.editIssue(projectId, issue.iid, { addLabels: [defaultScopedLabel] });
    }
};

const addBotComment = async (api: IssueBotAPI, projectId: string | number, issueIid: number, comment: string): Promise<void> => {
    const notes = await api.getComments(projectId, issueIid);
    const botNotes = notes.filter((n) => n.author.name.includes('Bot'));
    if (botNotes.length > 0) {
        // Use the most recent bot note
        const botNote = botNotes[botNotes.length - 1];
        // Append the new comment
        const body = botNote.body + '\n\n---\n\n' + comment;
        await api.editComment(projectId, issueIid, botNote.id, body);
    } else {
        // No existing bot comments, create a new one
        await api.createComment(projectId, issueIid, comment);
    }
};



// Example usage (for testing or standalone)
// const token = process.env.TOKEN_ISSUE_BOT;
// const payload = JSON.parse(process.env.PAYLOAD!);
// const platform = process.env.PLATFORM || 'gitlab'; // 'gitlab' or 'github'
// let api: IssueBotAPI;
// if (platform === 'gitlab') {
//     api = new GitLabAPI(new Gitlab({ token }));
// } else {
//     api = new GitHubAPI(new Octokit({ auth: token }));
// }
// issueBotHandler(api, payload);