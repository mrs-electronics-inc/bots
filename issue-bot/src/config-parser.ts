import * as fs from 'fs';
import { Label } from './apis';

const CONFIG_FILE_PATH = '.bots/labels.json';

export interface IssueBotConfig {
  typeLabels?: Record<string, Label>;
  validTypes?: string[];
  priorityLabels?: Label[];
  defaultPriorityLabel?: Label;
}

export function parseIssueBotConfig(): { config: IssueBotConfig; success: boolean } {
  if (!fs.existsSync(CONFIG_FILE_PATH)) {
    console.error('Could not find config file "%s".', CONFIG_FILE_PATH);
    return { config: {}, success: false };
  }

  const data = JSON.parse(fs.readFileSync(CONFIG_FILE_PATH, 'utf8'));
  let config: IssueBotConfig = {};

  // Parse type labels and valid types.
  if (data.typeLabels) {
    const typeLabelsData: Record<string, string> = data.typeLabels;
    const typeLabels: Record<string, Label> = Object.fromEntries(
      Object.entries(typeLabelsData).map(([key, value]) => [key, { name: value }])
    );
    config.typeLabels = typeLabels;
    config.validTypes = Object.keys(typeLabels);
  }

  // Parse priority labels.
  if (data.priorityLabels) {
    const priorityLabelsData: string[] = data.priorityLabels;
    config.priorityLabels = priorityLabelsData.map((value) => ({ name: value }));

    // If there is a configured default priority label then use it.
    // If not, then fallback to the first priority label.
    if (data.defaultPriorityLabel) {
      config.defaultPriorityLabel = { name: data.defaultPriorityLabel };
    } else {
      config.defaultPriorityLabel = config.priorityLabels[0];
    }
  }

  return { config, success: true };
}
