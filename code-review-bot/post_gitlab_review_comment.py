#!/usr/bin/env python3
import os
import sys
import gitlab


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
        with open('.bots/response/review.md', 'r') as f:
            review_content = f.read()
    except FileNotFoundError:
        print("Error: Review file not found", file=sys.stderr)
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


if __name__ == '__main__':
    main()
