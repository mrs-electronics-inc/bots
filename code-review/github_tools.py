import os
import json
import github

def get_details() -> str:
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        return json.dumps({"error": "Missing GitHub environment variables"})

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    pr = repo_obj.get_pull(int(pr_number))

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
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        return json.dumps({"error": "Missing GitHub environment variables"})

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    pr = repo_obj.get_pull(int(pr_number))

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
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        return json.dumps({"error": "Missing GitHub environment variables"})

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    pr = repo_obj.get_pull(int(pr_number))

    return '\n'.join(list(set(f.filename for f in pr.get_files())))

def get_diffs() -> str:
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        return json.dumps({"error": "Missing GitHub environment variables"})

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    pr = repo_obj.get_pull(int(pr_number))

    files = pr.get_files()
    diffs = []
    for f in files:
        diffs.append(f"diff --git a/{f.filename} b/{f.filename}\n{f.patch}")
    return '\n'.join(diffs)

def get_comments() -> str:
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        return json.dumps({"error": "Missing GitHub environment variables"})

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    pr = repo_obj.get_pull(int(pr_number))

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
    token = os.environ.get('GH_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    pr_number = os.environ.get('PULL_REQUEST_NUMBER')

    if not token or not repo or not pr_number:
        print("Missing GitHub environment variables")
        return

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    pr = repo_obj.get_pull(int(pr_number))

    pr.create_issue_comment(content)
    return "Created new GitHub comment"