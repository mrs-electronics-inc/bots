#!/usr/bin/env python3
import os
import sys
import gitlab
import github
import json


def main():
    platform = os.environ.get('PLATFORM', 'github')

    # Read the review content
    try:
        with open('.bots/response/review.json', 'r') as f:
            review = json.load(f)
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
        sys.exit(1)

    # Generate main comment
    main_comment = generate_main_comment(review)

    # Post comments
    if platform == "gitlab":
        post_gitlab_comments(main_comment, review["change_requests"])
    else:
        post_github_comments(main_comment, review["change_requests"])


def generate_main_comment(review):
    review_content = ""

    if len(review["change_requests"]) > 0:
        review_content += "# Changes Requested\n"
        review_content += "See below comments for specific change requests.\n"
        # TODO: remove this
        review_content += f"```json\n{review['change_requests']}\n```"
        review_content += "\n\n"
    else:
        review_content += "# Review\n"
        review_content += "No change requests.\n"

    if len(review["summary"]) > 0:
        review_content += "## Summary of Changes\n"
        review_content += review["summary"]
        review_content += "\n\n"

    if len(review["feedback"]) > 0:
        review_content += "## Overall Feedback\n"
        review_content += review["feedback"]
        review_content += "\n\n"

    return review_content


def post_gitlab_comments(main_comment, change_requests):
    # Get environment variables
    gitlab_token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    merge_request_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not all([gitlab_token, project_id, merge_request_iid]):
        print("Error: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Initialize GitLab client
    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=gitlab_token)

    try:
        # Get the project and merge request
        project = gl.projects.get(project_id)
        mr = project.mergerequests.get(merge_request_iid)

        # Get all notes (comments)
        notes = mr.notes.list(iterator=True)

        # Look for an existing comment from "Code Review Bot"
        comment_id = None
        for note in notes:
            if note.author.get('name') == 'Code Review Bot':
                comment_id = note.id
                break

        # Create or update the comment
        if comment_id:
            # Update existing comment
            note = mr.notes.get(comment_id)
            note.body = main_comment
            note.save()
            print(f"Updated comment with ID: {comment_id}")
        else:
            # Create new comment
            mr.notes.create({'body': main_comment})
            print("Created new comment")

        # TODO: add change requests comments

    except Exception as e:
        print(f"Error handling GitLab comment: {str(e)}", file=sys.stderr)
        sys.exit(1)


def post_github_comments(main_comment, change_requests):
    # Get environment variables
    github_token = os.environ.get('GH_TOKEN')
    pull_request_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not all([github_token, pull_request_number]):
        print("Error: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Initialize Github client
    gh = github.Github(auth=github.Auth.Token(github_token))

    # TODO: update existing comment, or create new one

    # TODO: add change request comments

    gh.close()


if __name__ == '__main__':
    main()
