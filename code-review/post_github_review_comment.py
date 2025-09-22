#!/usr/bin/env python3
import os
import sys
from github import Github
from comment_utils import read_review_content, read_response_content, is_review_comment


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
        review_content = read_review_content()
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
        sys.exit(1)

    # Read the response content if it exists
    response_content = read_response_content()

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
        for comment in comments:
            if comment.user.login in ['github-actions[bot]', 'Code Review Bot']:
                # Check if this is a review comment
                if is_review_comment(comment.body):
                    review_comment = comment
                    break

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
        if response_content:
            # Create new response comment
            pr.create_issue_comment(response_content)
            print("Created new response comment")

    except Exception as e:
        print(f"Error handling GitHub comment: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
