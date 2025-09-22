#!/usr/bin/env python3
import os
import sys
import subprocess
import json


def run_gh_command(command):
    """Run a GitHub CLI command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}", file=sys.stderr)
        print(f"Error output: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    # Get environment variables
    pr_ref = os.environ.get('GITHUB_HEAD_REF')
    if not pr_ref:
        print("Error: GITHUB_HEAD_REF environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Read the review content
    try:
        with open('.bots/response/review.md', 'r') as f:
            review_content = f.read()
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
        sys.exit(1)

    # Read the comments response content if it exists
    comments_content = None
    try:
        with open('.bots/response/comments.md', 'r') as f:
            content = f.read().strip()
            if content and content != "No new responses at this time.":
                comments_content = content
    except FileNotFoundError:
        pass  # No comments file is fine

    # Get existing comments from the PR
    comments_json = run_gh_command(f"gh pr comments {pr_ref} --json id,body,author")

    if comments_json:
        try:
            comments = json.loads(comments_json)
        except json.JSONDecodeError:
            print("Error parsing comments JSON", file=sys.stderr)
            sys.exit(1)
    else:
        comments = []

    # Look for existing comments from Code Review Bot
    review_comment_id = None
    comments_comment_id = None
    for comment in comments:
        author_login = comment.get('author', {}).get('login')
        if author_login in ['github-actions[bot]', 'Code Review Bot']:
            body = comment.get('body', '')
            # Check if this is a review comment
            if (body.startswith('# Changes Requested') or
                body.startswith('## Summary') or
                body.startswith('## Overall Feedback')):
                review_comment_id = comment.get('id')
            # Check if this is a comments response
            elif comments_content and body.strip() == comments_content.strip():
                comments_comment_id = comment.get('id')

    # Create or update the main review comment
    if review_comment_id is not None:
        # Update existing review comment
        print(f"Updating existing review comment with ID: {review_comment_id}")
        run_gh_command(f"gh pr comment {pr_ref} --edit {review_comment_id} -F .bots/response/review.md")
    else:
        # Create new review comment
        print("Creating new review comment")
        run_gh_command(f"gh pr comment {pr_ref} -F .bots/response/review.md")

    # Handle comment responses if they exist
    if comments_content:
        if comments_comment_id is not None:
            # Update existing comments comment
            print(f"Updating existing comments response with ID: {comments_comment_id}")
            # Write comments content to a temp file for the command
            with open('.bots/response/comments_temp.md', 'w') as f:
                f.write(comments_content)
            run_gh_command(f"gh pr comment {pr_ref} --edit {comments_comment_id} -F .bots/response/comments_temp.md")
            os.remove('.bots/response/comments_temp.md')
        else:
            # Create new comments comment
            print("Creating new comments response")
            # Write comments content to a temp file for the command
            with open('.bots/response/comments_temp.md', 'w') as f:
                f.write(comments_content)
            run_gh_command(f"gh pr comment {pr_ref} -F .bots/response/comments_temp.md")
            os.remove('.bots/response/comments_temp.md')


if __name__ == '__main__':
    main()