import llm
from typing import Optional
import os
import subprocess
import json
import github
import gitlab


def get_review_tools(context):
    return [get_details,
            get_commits_details,
            get_changed_files_tool(context),
            get_diffs_tool(context),
            get_file_contents,
            get_comments_tool(context),
            post_comment]


def get_details() -> str:
    """
    Get the overall details for the change request.
    """
    platform = os.environ.get('PLATFORM')
    if platform == 'github':
        return _get_github_details()
    elif platform == 'gitlab':
        return _get_gitlab_details()
    else:
        return "Unsupported platform"


def _get_github_details() -> str:
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


def _get_gitlab_details() -> str:
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
    """
    Get the details of all commits in the change request.
    """
    platform = os.environ.get('PLATFORM')
    if platform == 'github':
        return _get_github_commits_details()
    elif platform == 'gitlab':
        return _get_gitlab_commits_details()
    else:
        return "Unsupported platform"


def _get_github_commits_details() -> str:
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


def _get_gitlab_commits_details() -> str:
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


def get_changed_files_tool(context):
    def get_changed_files() -> str:
        """
        Get the file names of all the changed files.
        """
        # TODO: get changed files directly rather than from context object
        return context["changed_files"]
    return get_changed_files


def get_diffs_tool(context):
    def get_diffs() -> str:
        """
        Get the diffs for the change request.
        """
        # TODO: get diffs directly rather than from context object
        return context["diffs"]
    return get_diffs


def get_file_contents(file_name: str) -> str:
    """
    Get the current contents of the given file, with line numbers.
    """
    full_path = os.path.join("/repo", file_name)
    print("full path:", full_path)
    file_exists = os.path.exists(full_path)
    print("exists:", file_exists)
    if not file_exists:
        return "FILE DOES NOT EXIST"

    # Check if it's a text file
    try:
        result = subprocess.run(
            ['file', '-b', '--mime-type', full_path],
            capture_output=True,
            text=True,
            check=True
        )
        mime_type = result.stdout.strip()

        if not mime_type.startswith('text/'):
            return f"FILE HAS UNSUPPORTED MIME TYPE: {mime_type}"

        # Check line count
        with open(full_path, 'r') as f:
            lines = f.readlines()

        if len(lines) >= 1000:
            return f"FILE IS TOO BIG: {len(lines)} lines"

        # Read file content using batcat so it includes line numbers
        batcat_result = subprocess.run(
            ['batcat', '--style=numbers,plain',
                '--decorations=always', full_path],
            capture_output=True,
            text=True,
            check=True
        )

        return batcat_result.stdout

    except Exception:
        return "ERROR READING FILE"


def get_comments_tool(context):
    def get_comments() -> str:
        """
        Get the comments for the change request.
        NOTE: this will not include any newly added comments.
        """
        # TODO: get comments directly rather than from context object
        return context["comments"]
    return get_comments


def post_comment(content: str):
    """
    Post a comment on the change request.
    """
    platform = os.environ.get('PLATFORM')
    if platform == 'github':
        _post_github_comment(content)
    elif platform == 'gitlab':
        _post_gitlab_comment(content)
    else:
        print(f"Unsupported platform: {platform}")
        return


def _post_github_comment(content: str):
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


def _post_gitlab_comment(content: str):
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


def before_tool_call(tool: Optional[llm.Tool], tool_call: llm.ToolCall):
    tool_name = tool.name if tool else "unknown"
    print(f"Calling tool {tool_name} with arguments {tool_call.arguments}")


def after_tool_call(tool: llm.Tool, tool_call: llm.ToolCall,
                    tool_result: llm.ToolResult):
    print(
        f"Called tool {tool.name} with arguments {tool_call.arguments}, returned {tool_result.output}")
