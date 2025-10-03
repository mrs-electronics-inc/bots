#!/usr/bin/env python3
"""
Collect context for code review and save as JSON.

This script collects context for code review from either GitLab or GitHub,
including details, comments, and diffs, and saves them as JSON.
"""
import os
import json
import sys


def read_context_file(file_path):
    """Read content from a context file."""
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.json'):
                return json.load(f)
            else:
                return f.read()
    except FileNotFoundError:
        print(f"Warning: Context file not found: {file_path}", file=sys.stderr)
        return ""


def main():
    """Main function to collect context."""
    # Read context from files
    context = {}
    context['comments'] = read_context_file('.bots/context/comments.json')
    context['diffs'] = read_context_file('.bots/context/diffs')



    # Save context as JSON
    output_path = '.bots/context.json'
    try:
        with open(output_path, 'w') as f:
            json.dump(context, f, indent=2)
        print(f"Context saved to {output_path}")
    except Exception as e:
        print(f"Error saving context: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
