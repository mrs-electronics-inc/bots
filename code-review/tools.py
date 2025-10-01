import llm
from typing import Optional
import os
import subprocess


def get_review_tools(context):
    return [get_details_tool(context),
            get_changed_files_tool(context),
            get_diffs_tool(context),
            get_file_contents,
            get_comments_tool(context),
            post_comment]


def get_details_tool(context):
    def get_details() -> str:
        """
        Get the overall details for the change request.
        """
        # TODO: get details directly rather than from context object
        return context["details"]


def get_changed_files_tool(context):
    def get_changed_files() -> str:
        """
        Get the file names of all the changed files.
        """
        # TODO: get changed files directly rather than from context object
        return context["changed_files"]


def get_diffs_tool(context):
    def get_diffs() -> str:
        """
        Get the diffs for the change request.
        """
        # TODO: get diffs directly rather than from context object
        return context["diffs"]


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
            return f"FILE HAS UNSUPPORTED MIME TYPE: ${mime_type}"

        # Check line count
        with open(full_path, 'r') as f:
            lines = f.readlines()

        if len(lines) >= 1000:
            return f"FILE IS TOO BIG: ${len(lines)} lines"

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


def post_comment(content: str):
    """
    Post a comment on the change request.
    """
    # TODO: actually implement posting the comment
    print('new comment:', content)


def before_tool_call(tool: Optional[llm.Tool], tool_call: llm.ToolCall):
    print(f"Calling tool {tool.name} with arguments {tool_call.arguments}")


def after_tool_call(tool: llm.Tool, tool_call: llm.ToolCall,
                    tool_result: llm.ToolResult):
    print(
        f"Called tool {tool.name} with arguments {tool_call.arguments}, returned {tool_result.output}")
