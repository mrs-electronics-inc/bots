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


def collect_gitlab_context():
    """Collect context from GitLab merge request."""
    context = {}

    # Get environment variables
    project_id = os.getenv('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.getenv('CI_MERGE_REQUEST_IID')
    target_branch = os.getenv('CI_MERGE_REQUEST_TARGET_BRANCH_NAME')

    if not all([project_id, mr_iid, target_branch]):
        print("Error: Missing required GitLab environment variables", file=sys.stderr)
        sys.exit(1)

    # Collect merge request details
    context['details'] = run_command(f"glab mr view {mr_iid}")

    # Collect merge request comments
    comments_cmd = f"glab api \"projects/{project_id}/merge_requests/{mr_iid}/notes\""
    comments_json = run_command(comments_cmd)
    context['comments'] = comments_json

    # Collect diffs
    context['diffs'] = run_command(f"glab mr diff {mr_iid} --raw")

    # Collect changed files
    run_command(f"git fetch origin {target_branch}")
    changed_files = run_command(f"git diff origin/{target_branch} --name-only")
    context['changed_files'] = changed_files.split(
        '\n') if changed_files else []

    return context


def collect_github_context():
    """Collect context from GitHub pull request."""
    context = {}

    # Get environment variables
    head_ref = os.getenv('GITHUB_HEAD_REF')
    repository = os.getenv('GITHUB_REPOSITORY')
    pr_number = os.getenv('PULL_REQUEST_NUMBER')

    if not all([head_ref, repository, pr_number]):
        print("Error: Missing required GitHub environment variables", file=sys.stderr)
        sys.exit(1)

    # Collect pull request details
    context['details'] = run_command(f"gh pr view {head_ref}")

    # Collect pull request comments
    comments_cmd = f"gh api \"repos/{repository}/issues/{pr_number}/comments\""
    comments_json = run_command(comments_cmd)
    context['comments'] = comments_json

    # Collect diffs
    context['diffs'] = run_command(f"gh pr diff {head_ref}")

    # Collect changed files
    changed_files = run_command(f"gh pr diff {head_ref} --name-only")
    context['changed_files'] = changed_files.split(
        '\n') if changed_files else []

    return context


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

    # Get platform
    platform = os.getenv('PLATFORM')
    if platform not in ['gitlab', 'github']:
        print(f"Error: unknown platform: ${platform}", file=sys.stderr)
        sys.exit(1)

    # Collect context based on platform
    if platform == 'gitlab':
        context = collect_gitlab_context()
    else:
        context = collect_github_context()

    # Collect file contents
    file_contents = collect_file_contents(context.get('changed_files', []))
    context['file_contents'] = file_contents

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
