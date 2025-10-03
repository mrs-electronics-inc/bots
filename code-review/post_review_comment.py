#!/usr/bin/env python3
import os
import sys
import gitlab
import github


# Prefixes used to identify review comments
REVIEW_COMMENT_PREFIXES = [
    '# Review',
    '# Changes Requested',
]


def post_github_comment():
    """Post or update comment on GitHub PR."""
    token = os.environ.get('GH_TOKEN')
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not all([token, repo_name, pr_number]):
        print("Error: Missing required environment variables (GH_TOKEN, GITHUB_REPOSITORY, PULL_REQUEST_NUMBER)", file=sys.stderr)
        sys.exit(1)

    # Read the review content
    try:
        with open('.bots/response/review.md', 'r') as f:
            review_content = f.read()
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
        sys.exit(1)

    try:
        g = github.Github(auth=github.Auth.Token(token))
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))

        # Get all comments on the PR
        comments = list(pr.get_issue_comments())

        # Look for an existing review comment
        bot_comment = None
        for comment in reversed(comments):
            if (comment.user.login == 'github-actions[bot]'
                    and is_review_comment(comment.body)):
                bot_comment = comment
                break

        if bot_comment:
            # Update existing comment
            bot_comment.edit(review_content)
            print(f"Updated comment with ID: {bot_comment.id}")
        else:
            # Create new comment
            pr.create_issue_comment(review_content)
            print("Created new comment")

    except Exception as e:
        print(f"Error handling GitHub comment: {str(e)}", file=sys.stderr)
        sys.exit(1)


def post_gitlab_comment():
    """Post or update comment on GitLab MR."""
    # Get environment variables
    gitlab_token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    merge_request_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not all([gitlab_token, project_id, merge_request_iid]):
        print("Error: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Read the review content
    try:
        with open('.bots/response/review.md', 'r') as f:
            review_content = f.read()
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize GitLab client
        gl = gitlab.Gitlab(url='https://gitlab.com',
                           private_token=gitlab_token)

        # Get the project and merge request
        project = gl.projects.get(project_id)
        mr = project.mergerequests.get(merge_request_iid)

        # Get all notes (comments)
        notes = mr.notes.list(iterator=True)

        # Look for an existing review comment
        comment_id = None
        for note in notes:
            if (note.author.get('name') == 'Code Review Bot'
                    and is_review_comment(note.body)):
                comment_id = note.id
                break

        # Create or update the comment
        if comment_id:
            # Update existing comment
            note = mr.notes.get(comment_id)
            note.body = review_content
            note.save()
            print(f"Updated comment with ID: {comment_id}")
        else:
            # Create new comment
            mr.notes.create({'body': review_content})
            print("Created new comment")

    except Exception as e:
        print(f"Error handling GitLab comment: {str(e)}", file=sys.stderr)
        sys.exit(1)


def is_review_comment(body):
    """Check if a comment body is a review comment based on prefixes"""
    return any(body.startswith(prefix) for prefix in REVIEW_COMMENT_PREFIXES)


def main():
    platform = os.environ.get('PLATFORM')
    if platform == 'github':
        post_github_comment()
    elif platform == 'gitlab':
        post_gitlab_comment()
    else:
        print("Error: PLATFORM environment variable must be 'github' or 'gitlab'", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
