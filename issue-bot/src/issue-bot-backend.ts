import { IssueBotAPI, Issue, Label } from './apis';
import { parseIssueBotConfig } from './config-parser';

// This is the name that the bot should have in projects,
// assuming users follow the setup steps correctly.
const ISSUE_BOT_NAME = 'Issue Bot';

// eslint-disable-next-line no-undef
var logger: Console = {
  ...console,
  log: () => undefined,
  debug: () => undefined,
  info: () => undefined,
};

export interface IssueBotOptions {
  silent?: boolean;
  verbose?: boolean;
  help?: boolean;
}

export const issueBotHandler = async (
  api: IssueBotAPI,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  event: any,
  options?: IssueBotOptions
): Promise<{ success: boolean; timestamp?: number }> => {
  // If we are instructed to be verbose then allow regular messages to go to the console too
  // instead of just warning and error messages.
  if (options?.verbose) {
    logger.log = console.log;
    logger.debug = console.debug;
    logger.info = console.info;
  }
  // If we are instructed to be silent then do not allow any messages to go through.
  // Note that silent and verbose are mutually exclusive options.
  else if (options?.silent) {
    logger.error = () => undefined;
    logger.warn = () => undefined;
  }

  // Make sure a valid issue event was actually passed.
  if (!event) {
    logger.error('No event was passed!');
    return { success: false };
  }
  logger.log('Event:', event);
  const parsedEvent = api.parseIssueEvent(event);
  if (!parsedEvent) {
    logger.warn('Ignoring this event, it is irrelevant');
    return { success: false };
  }

  // Prevent a loop of bots triggering more bots.
  if (parsedEvent.user.name.includes(ISSUE_BOT_NAME)) {
    logger.warn('Handler triggered by another issue bot. Exiting early.');
    return { success: false };
  }

  logger.log('project/repo id: %s issue id: %s', parsedEvent.project.id, parsedEvent.issue.id);

  const issue: Issue = await api.getIssue(parsedEvent.project.id, parsedEvent.issue.id);

  // Do not do anything to closed issues.
  if (issue.state === 'closed') {
    logger.warn('Leaving early, this issue is closed.');
    return { success: false };
  }

  // Parse out the issue bot configuration. Return early if there was a problem doing so.
  const { config, success: ok } = parseIssueBotConfig();
  if (!ok) {
    logger.error('Could not parse issue bot configuration!!');
    return { success: false };
  }

  if (config.typeLabels && config.validTypes) {
    await checkIssueType(api, issue, config.validTypes, config.typeLabels);
  }

  if (config.priorityLabels && config.defaultPriorityLabel) {
    await checkHasRequiredLabel(api, issue, config.priorityLabels, config.defaultPriorityLabel);
  }

  // TODO: apply epic label, or leave comment if epic is missing

  return { success: true, timestamp: Date.now() };
};

// Verify that the given issue has a valid type, as determined by the prefix on the issue title.
// If it doesn't, then add a comment on the issue to let the user know there's a problem.
// If it does, but doesn't have the corresponding label, then add the label.
const checkIssueType = async (
  api: IssueBotAPI,
  issue: Issue,
  validTypes: string[],
  typeLabels: Record<string, Label>
): Promise<void> => {
  const issueType = extractIssueType(issue.title, validTypes);
  if (issueType == null) {
    logger.error('issue must have a valid type!');
    let comment = 'The issue title must begin with one of the following prefixes:\n';
    for (const type of validTypes) {
      comment += `   - ${type}\n`;
    }
    await addBotComment(api, issue, comment);
  } else {
    logger.log('issue type:', issueType);
    const label = typeLabels[issueType];
    if (!issue.labels.map((l) => l.name).includes(label.name)) {
      await api.editIssue(issue.projectId, issue.id, { addLabel: label });
    }
  }
};

const extractIssueType = (issueTitle: string, validTypes: string[]): string | null => {
  const match = issueTitle.match(/^(\w+)(?:\(.*?\))?:/);

  if (match) {
    const type = match[1];
    return validTypes.includes(type) ? type : null;
  }

  return null;
};

const checkHasRequiredLabel = async (
  api: IssueBotAPI,
  issue: Issue,
  labelList: Label[],
  defaultLabel: Label
): Promise<void> => {
  logger.log(
    'required label list:',
    labelList.map((l) => l.name)
  );
  logger.log('default label:', defaultLabel.name);

  // Determine whether the given issue has one of the labels from the required list already.
  const hasRequiredLabel = issue.labels.some((l) => labelList.includes(l));

  // If it does not, then add the default.
  // Add a comment on the issue explaining what happened.
  if (!hasRequiredLabel) {
    let comment = 'The issue must have one of the following labels:\n';
    for (const label of labelList) {
      comment += `- ~"${label.name}"\n`;
    }
    comment += `\n\nI am assigning the default label ~"${defaultLabel.name}". Please replace with the correct label if needed.`;
    await addBotComment(api, issue, comment);
    await api.editIssue(issue.projectId, issue.id, { addLabel: defaultLabel });
  }
};

const addBotComment = async (api: IssueBotAPI, issue: Issue, comment: string): Promise<void> => {
  const notes = await api.getComments(issue.projectId, issue.id);
  const botNotes = notes.filter((n) => n.author.name.includes(ISSUE_BOT_NAME));
  if (botNotes.length > 0) {
    // Use the most recent bot note
    const botNote = botNotes[botNotes.length - 1];
    // Append the new comment
    const body = botNote.body + '\n\n---\n\n' + comment;
    await api.editComment(issue.projectId, issue.id, botNote.id, body);
  } else {
    // No existing bot comments, create a new one
    await api.createComment(issue.projectId, issue.id, comment);
  }
};
