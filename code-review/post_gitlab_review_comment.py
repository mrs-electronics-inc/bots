#!/usr/bin/env python3
import os
import sys
import gitlab
from comment_utils import read_review_content, read_response_content, is_review_comment


def main():
    # Get environment variables
    gitlab_token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    merge_request_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not all([gitlab_token, project_id, merge_request_iid]):
        print("Error: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Read the review content
    try:
        review_content = read_review_content()
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
        sys.exit(1)

    # Read the response content if it exists
    response_content = read_response_content()

    # Initialize GitLab client
    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=gitlab_token)

    try:
        # Get the project and merge request
        project = gl.projects.get(project_id)
        mr = project.mergerequests.get(merge_request_iid)

        # Get all notes (comments)
        notes = mr.notes.list(iterator=True)

        # Look for existing comments from "Code Review Bot"
        review_comment_id = None
        for note in notes:
            if note.author.get('name') == 'Code Review Bot':
                # Check if this is a review comment
                if is_review_comment(note.body):
                    review_comment_id = note.id
                    break

        # Create or update the main review comment
        if review_comment_id is not None:
            # Update existing review comment
            note = mr.notes.get(int(review_comment_id))
            note.body = review_content
            note.save()
            print(f"Updated review comment with ID: {review_comment_id}")
        else:
            # Create new review comment
            mr.notes.create({'body': review_content})
            print("Created new review comment")

        # Handle comment responses if they exist
        if response_content:
            # Create new response comment
            mr.notes.create({'body': response_content})
            print("Created new comments response")

    except Exception as e:
        print(f"Error handling GitLab comment: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
