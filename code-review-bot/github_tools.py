import os
import json
import github
import utils

# This is currently the only support bot username for now.
# In the future we may make this configurable.
BOT_USERNAME = "github-actions[bot]"


def get_details() -> str:
    """
    Get the overall details for the change request.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    return json.dumps(
        {
            "id": pr.number,
            "title": pr.title,
            "description": pr.body,
            "author": pr.user.login,
            "state": pr.state,
            "created_at": pr.created_at.isoformat(),
            "url": pr.html_url,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
        }
    )


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
        commit_list.append(
            {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": (
                    commit.commit.author.name if commit.commit.author else None
                ),
                "date": (
                    commit.commit.author.date.isoformat()
                    if commit.commit.author
                    else None
                ),
                "url": commit.html_url,
            }
        )

    return json.dumps(commit_list)


def get_changed_files() -> str:
    """
    Get the file names of all the changed files.
    """
    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    return json.dumps(list(set(f.filename for f in pr.get_files())))


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
    return json.dumps({"diffs": "\n".join(diffs)})


def get_comments_api() -> str:
    """
    Low-level access to GitLab comments for a merge request.
    """
    pr = _get_pr()
    if pr is None:
        return {"error": "Missing GitHub environment variables"}

    # get_issue_comments returns the comments in the main conversation section
    conversation_comments = pr.get_issue_comments()
    # get_review_comments returns the comments in the files section
    review_comments = pr.get_review_comments()
    comments = list(conversation_comments) + list(review_comments)
    comments.sort(key=lambda c: c.created_at)
    comment_list = []
    for c in comments:
        comment_list.append(
            {
                "username": c.user.login,
                "timestamp": c.created_at.isoformat(),
                "body": c.body,
                "id": c.id,
            }
        )
    return comment_list


def post_comment_api(content: str):
    """
    Used by tools.create_post_comment_tool to create a tool
    to post comments to GitHub
    """
    pr = _get_pr()
    if pr is None:
        return {"error": "Missing GitHub environment variables"}

    pr.create_issue_comment(content)
    return {"success": "Created new GitHub comment"}


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
        return json.dumps({"error": error})

    pr = _get_pr()
    if pr is None:
        return json.dumps({"error": "Missing GitHub environment variables"})

    # Get all "issue comments" on the PR
    # We ONLY need to check the "issue comments" because those are the ONLY way
    # we post the overall review comments
    comments = list(pr.get_issue_comments())

    # Look for an existing review comment
    bot_comment = None
    for comment in reversed(comments):
        is_author = comment.user.login == BOT_USERNAME
        if is_author and utils.is_review_comment(comment.body):
            bot_comment = comment
            break

    if bot_comment:
        # Update existing comment
        bot_comment.edit(content)
        return json.dumps({"success": f"Updated comment {bot_comment.id}"})
    else:
        # Create new comment
        pr.create_issue_comment(content)
        return json.dumps({"success": "Created new comment"})


def _get_pr():
    token = os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PULL_REQUEST_NUMBER")

    if not token or not repo or not pr_number:
        return None

    g = github.Github(token)
    repo_obj = g.get_repo(repo)
    return repo_obj.get_pull(int(pr_number))
