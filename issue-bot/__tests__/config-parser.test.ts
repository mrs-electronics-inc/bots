import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import * as fs from 'fs';
import { parseIssueBotConfig } from '../src/config-parser';

jest.mock('fs');

const mockedFs = fs as jest.Mocked<typeof fs>;

// Mute output
console.error = jest.fn();

describe('config parser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fail when config file does not exist', () => {
    mockedFs.existsSync.mockReturnValue(false);

    const result = parseIssueBotConfig();

    expect(result).toEqual({ config: {}, success: false });
  });

  it('should parse typeLabels and validTypes correctly', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({
        typeLabels: {
          fix: 'Type::Bug',
          feat: 'Type::Feature',
          docs: 'Type::Documentation',
        },
      })
    );

    const result = parseIssueBotConfig();

    expect(result.success).toBe(true);
    expect(result.config.typeLabels).toEqual({
      fix: { name: 'Type::Bug' },
      feat: { name: 'Type::Feature' },
      docs: { name: 'Type::Documentation' },
    });
    expect(result.config.validTypes).toEqual(['fix', 'feat', 'docs']);
  });

  it('should parse priorityLabels with defaultPriorityLabel', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({
        priorityLabels: ['Priority::Low', 'Priority::Medium', 'Priority::High'],
        defaultPriorityLabel: 'Priority::Medium',
      })
    );

    const result = parseIssueBotConfig();

    expect(result.success).toBe(true);
    expect(result.config.priorityLabels).toEqual([
      { name: 'Priority::Low' },
      { name: 'Priority::Medium' },
      { name: 'Priority::High' },
    ]);
    expect(result.config.defaultPriorityLabel).toEqual({ name: 'Priority::Medium' });
  });

  it('should parse priorityLabels and use first label as default if no defaultPriorityLabel specified', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({
        priorityLabels: ['Priority::Low', 'Priority::Medium', 'Priority::High'],
      })
    );

    const result = parseIssueBotConfig();

    expect(result.success).toBe(true);
    expect(result.config.priorityLabels).toEqual([
      { name: 'Priority::Low' },
      { name: 'Priority::Medium' },
      { name: 'Priority::High' },
    ]);
    expect(result.config.defaultPriorityLabel).toEqual({ name: 'Priority::Low' });
  });

  it('should parse both typeLabels and priorityLabels', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({
        typeLabels: {
          fix: 'Type::Bug',
          feat: 'Type::Feature',
          docs: 'Type::Documentation',
        },
        priorityLabels: ['Priority::Low', 'Priority::High'],
        defaultPriorityLabel: 'Priority::Low',
      })
    );

    const result = parseIssueBotConfig();

    expect(result.success).toBe(true);
    expect(result.config.typeLabels).toEqual({
      fix: { name: 'Type::Bug' },
      feat: { name: 'Type::Feature' },
      docs: { name: 'Type::Documentation' },
    });
    expect(result.config.validTypes).toEqual(['fix', 'feat', 'docs']);
    expect(result.config.priorityLabels).toEqual([
      { name: 'Priority::Low' },
      { name: 'Priority::High' },
    ]);
    expect(result.config.defaultPriorityLabel).toEqual({ name: 'Priority::Low' });
  });

  it('should handle empty config file', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(JSON.stringify({}));

    const result = parseIssueBotConfig();

    expect(result.success).toBe(true);
    expect(result.config).toEqual({});
  });

  it('should throw error on invalid JSON', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue('invalid json');

    expect(() => parseIssueBotConfig()).toThrow(SyntaxError);
  });
});
