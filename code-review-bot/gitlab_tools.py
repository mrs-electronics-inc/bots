import os
import json
import gitlab
import subprocess
import utils


def get_details() -> str:
    """
    Get the overall details for the change request.
    """
    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    return json.dumps(
        {
            "id": mr.iid,
            "title": mr.title,
            "description": mr.description,
            "author": mr.author["username"],
            "state": mr.state,
            "created_at": mr.created_at,
            "url": mr.web_url,
            "base_branch": mr.target_branch,
            "head_branch": mr.source_branch,
        }
    )


def get_commits_details() -> str:
    """
    Get the details of all commits in the change request.
    """
    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    commits = mr.commits()
    commit_list = []
    for commit in commits:
        commit_list.append(
            {
                "sha": commit.id,
                "message": commit.message,
                "author": commit.author_name,
                "date": commit.authored_date,
                "url": commit.web_url,
            }
        )

    return json.dumps(commit_list)


def get_changed_files() -> str:
    """
    Get the file names of all the changed files.
    """
    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    changes = mr.changes()
    changed_files = list(
        set([change["new_path"] for change in changes["changes"]])
    )
    return json.dumps(changed_files)


def get_diffs() -> str:
    """
    Get the diffs for the change request.
    """
    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    # The GitLab API doesn't provide a simple way to get diffs,
    # so we use the CLI
    result = subprocess.run(
        ["glab", "mr", "diff", str(mr.iid)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def get_comments() -> str:
    """
    Get the comments for the change request.
    """
    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    notes = mr.notes.list(get_all=True)
    # Reverse to oldest first
    notes.reverse()
    comment_list = []
    for n in notes:
        comment_list.append(
            {
                "username": n.author["username"],
                "name": n.author["name"],
                "timestamp": n.created_at,
                "body": n.body,
                "id": n.id,
            }
        )
    return json.dumps(comment_list)


@utils.rate_limit_tool(
    limit=5,
    error="You have already posted the maximum number of comments for this review session. DO NOT try again!",
)
def post_comment(content: str, reason: str):
    """
    Post a comment on the change request.
    Reason must be one of the following:
        - "suggestion"
        - "clarification"
        - "warning"
        - "response"
    """
    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    error = utils.verify_comment_reason(reason)
    if error:
        return {"error": error}

    mr.notes.create({"body": content})
    return json.dumps({"success": "Created new GitLab comment"})


@utils.rate_limit_tool(
    limit=1,
    error="You have already posted the overall review comment for this review session. DO NOT try again!",
)
def post_review(content: str):
    """
    Update the overall review comment.
    Creates a new review comment if one doesn't exist yet.
    """
    error = utils.verify_review_content(content)
    if error:
        return {"error": error}

    mr = _get_mr()
    if mr is None:
        return json.dumps({"error": "Missing GitLab environment variables"})

    # Get all notes (comments)
    notes = mr.notes.list(iterator=True)

    # Look for an existing review comment
    comment_id = None
    for note in notes:
        is_author = note.author.get("name") == "Code Review Bot"
        if is_author and utils.is_review_comment(note.body):
            comment_id = note.id
            break

    # Create or update the comment
    if comment_id:
        # Update existing comment
        note = mr.notes.get(comment_id)
        note.body = content
        note.save()
        return json.dumps({"success": f"Updated comment with ID: {comment_id}"})
    else:
        # Create new comment
        mr.notes.create({"body": content})
        return json.dumps({"success": f"Created new comment"})


def _get_mr():
    token = os.environ.get("GITLAB_TOKEN")
    project_id = os.environ.get("CI_MERGE_REQUEST_PROJECT_ID")
    mr_iid = os.environ.get("CI_MERGE_REQUEST_IID")

    if not token or not project_id or not mr_iid:
        return None

    gl = gitlab.Gitlab(url="https://gitlab.com", private_token=token)
    project = gl.projects.get(project_id)
    return project.mergerequests.get(mr_iid)
