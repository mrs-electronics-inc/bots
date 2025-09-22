#!/usr/bin/env python3
import os
import sys
from github import Github


def main():
    # Get environment variables
    github_token = os.environ.get('GITHUB_TOKEN')
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not all([github_token, repo_name, pr_number]):
        print("Error: Missing required environment variables: GITHUB_TOKEN, GITHUB_REPOSITORY, PULL_REQUEST_NUMBER", file=sys.stderr)
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

    # Initialize GitHub client
    g = Github(github_token)

    try:
        # Get the repository and pull request
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(pr_number))

        # Get all comments on the PR
        comments = list(pr.get_issue_comments())

        # Look for existing comments from Code Review Bot
        review_comment = None
        comments_comment = None
        for comment in comments:
            if comment.user.login in ['github-actions[bot]', 'Code Review Bot']:
                body = comment.body
                # Check if this is a review comment
                if (body.startswith('# Changes Requested') or
                    body.startswith('## Summary') or
                    body.startswith('## Overall Feedback')):
                    review_comment = comment
                # Check if this is a comments response
                elif comments_content and body.strip() == comments_content.strip():
                    comments_comment = comment

        # Create or update the main review comment
        if review_comment is not None:
            # Update existing review comment
            review_comment.edit(body=review_content)
            print(f"Updated review comment with ID: {review_comment.id}")
        else:
            # Create new review comment
            pr.create_issue_comment(review_content)
            print("Created new review comment")

        # Handle comment responses if they exist
        if comments_content:
            if comments_comment is not None:
                # Update existing comments comment
                comments_comment.edit(body=comments_content)
                print(f"Updated comments response with ID: {comments_comment.id}")
            else:
                # Create new comments comment
                pr.create_issue_comment(comments_content)
                print("Created new comments response")

    except Exception as e:
        print(f"Error handling GitHub comment: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()