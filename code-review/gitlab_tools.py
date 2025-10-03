import os
import json
import gitlab

def get_details() -> str:
    token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not token or not project_id or not mr_iid:
        return json.dumps({"error": "Missing GitLab environment variables"})

    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=token)
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    return json.dumps({
        "id": mr.iid,
        "title": mr.title,
        "description": mr.description,
        "author": mr.author['username'],
        "state": mr.state,
        "created_at": mr.created_at.isoformat(),
        "url": mr.web_url,
        "base_branch": mr.target_branch,
        "head_branch": mr.source_branch
    })

def get_commits_details() -> str:
    token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not token or not project_id or not mr_iid:
        return json.dumps({"error": "Missing GitLab environment variables"})

    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=token)
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    commits = mr.commits()
    commit_list = []
    for commit in commits:
        commit_list.append({
            "sha": commit.id,
            "message": commit.message,
            "author": commit.author_name,
            "date": commit.authored_date,
            "url": commit.web_url
        })

    return json.dumps(commit_list)

def get_changed_files() -> str:
    token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not token or not project_id or not mr_iid:
        return json.dumps({"error": "Missing GitLab environment variables"})

    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=token)
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    return '\n'.join(list(set(mr.changes().keys())))

def get_diffs() -> str:
    token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not token or not project_id or not mr_iid:
        return json.dumps({"error": "Missing GitLab environment variables"})

    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=token)
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    diffs = mr.diffs.list()
    diff_texts = [d.diff for d in diffs]
    return '\n'.join(diff_texts)

def get_comments() -> str:
    token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not token or not project_id or not mr_iid:
        return json.dumps({"error": "Missing GitLab environment variables"})

    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=token)
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    notes = mr.notes.list()
    # Reverse to oldest first
    notes.reverse()
    comment_list = []
    for n in notes:
        comment_list.append({
            "username": n.author['username'],
            "name": n.author['name'],
            "timestamp": n.created_at,
            "body": n.body,
            "id": n.id
        })
    return json.dumps(comment_list)

def post_comment(content: str):
    token = os.environ.get('GITLAB_TOKEN')
    project_id = os.environ.get('CI_MERGE_REQUEST_PROJECT_ID')
    mr_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    if not token or not project_id or not mr_iid:
        print("Missing GitLab environment variables")
        return

    gl = gitlab.Gitlab(url='https://gitlab.com', private_token=token)
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    mr.notes.create({'body': content})
    return "Created new GitLab comment"