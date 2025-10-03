import os
import json
import github


def get_details() -> str:
    """
    Get the overall details for the change request.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    return json.dumps({
        "id": pr.number,
        "title": pr.title,
        "description": pr.body,
        "author": pr.user.login,
        "state": pr.state,
        "created_at": pr.created_at.isoformat(),
        "url": pr.html_url,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref
    })


def get_commits_details() -> str:
    """
    Get the details of all commits in the change request.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    commits = pr.get_commits()
    commit_list = []
    for commit in commits:
        commit_list.append({
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": commit.commit.author.name if commit.commit.author else None,
            "date": commit.commit.author.date.isoformat() if commit.commit.author else None,
            "url": commit.html_url
        })

    return json.dumps(commit_list)


def get_changed_files() -> str:
    """
    Get the file names of all the changed files.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    return '\n'.join(list(set(f.filename for f in pr.get_files())))


def get_diffs() -> str:
    """
    Get the diffs for the change request.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    files = pr.get_files()
    diffs = []
    for f in files:
        diffs.append(f"diff --git a/{f.filename} b/{f.filename}\n{f.patch}")
    return '\n'.join(diffs)


def get_comments() -> str:
    """
    Get the comments for the change request.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    comments = pr.get_comments()
    comment_list = []
    for c in comments:
        comment_list.append({
            "username": c.user.login,
            "timestamp": c.created_at.isoformat(),
            "body": c.body,
            "id": c.id
        })
    return json.dumps(comment_list)


def post_comment(content: str):
    """
    Post a comment on the change request.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    pr.create_issue_comment(content)
    return json.dumps({"success": "Created new GitHub comment"})


def _get_pr():
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        return None

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    return repo_obj.get_pull(int(pr_number))
