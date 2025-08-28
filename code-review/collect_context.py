#!/usr/bin/env python3
"""
Collect context for code review and save as JSON.

This script collects context for code review from either GitLab or GitHub,
including details, comments, diffs, and file contents, and saves them as JSON.
"""
import os
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def read_context_file(file_path):
    """Read content from a context file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Context file not found: {file_path}", file=sys.stderr)
        return ""


def collect_file_contents(changed_files, max_count=10, max_lines=400):
    """Collect contents of changed files."""
    file_contents = {}
    count = 0

    for file_path in changed_files:
        if count >= max_count:
            break

        file_path = file_path.strip()
        if not file_path or not os.path.isfile(file_path):
            continue

        # Check if it's a text file
        try:
            result = subprocess.run(
                ['file', '-b', '--mime-type', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            mime_type = result.stdout.strip()

            if not mime_type.startswith('text/'):
                continue

            # Check line count
            with open(file_path, 'r') as f:
                lines = f.readlines()

            if len(lines) >= max_lines:
                continue

            # Read file content
            with open(file_path, 'r') as f:
                content = f.read()

            file_contents[file_path] = content
            count += 1

        except Exception as e:
            print(f"Error processing file {file_path}: {e}", file=sys.stderr)
            continue

    return file_contents


def main():
    """Main function to collect context."""
    print("Collecting context...")

    # Create .bots/context directory if it doesn't exist
    context_dir = Path('.bots/context')
    context_dir.mkdir(parents=True, exist_ok=True)

    # Read context from files
    context = {}
    context['details'] = read_context_file('.bots/context/details')
    context['comments'] = read_context_file('.bots/context/comments')
    context['diffs'] = read_context_file('.bots/context/diffs')

    # Extract changed files from diffs
    # This is a simple approach - we look for lines that start with "+++ " or "--- "
    # which indicate file paths in unified diff format
    changed_files = []
    if context['diffs']:
        for line in context['diffs'].split('\n'):
            if line.startswith('+++ b/') or line.startswith('--- a/'):
                file_path = line.split('/', 1)[1]
                if file_path not in changed_files:
                    changed_files.append(file_path)

    # Collect file contents
    file_contents = collect_file_contents(changed_files)
    context['file_contents'] = file_contents
    context['changed_files'] = changed_files

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
