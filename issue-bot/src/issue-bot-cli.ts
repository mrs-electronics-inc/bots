import { Gitlab } from '@gitbeaker/rest';
import { GitLabAPI } from './apis';
import { issueBotHandler, IssueBotOptions } from './issue-bot-backend';
import { parse } from 'ts-command-line-args';

async function main() {
  // Parse out the command-line arguments.
  const options = parse<IssueBotOptions>(
    {
      verbose: { type: Boolean, optional: true, description: 'Print all logging information' },
      help: { type: Boolean, optional: true, alias: 'h', description: 'Prints this usage guide' },
    },
    {
      helpArg: 'help',
      headerContentSections: [
        { header: 'MRS Issue Bot', content: 'Automated tooling for Gitlab issue management' },
      ],
    }
  );

  const token = process.env.TOKEN_ISSUE_BOT!;
  const payload = JSON.parse(process.env.PAYLOAD!);
  let api = new GitLabAPI(new Gitlab({ token }));
  return await issueBotHandler(api, payload, options);
}

main();
