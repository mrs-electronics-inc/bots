import llm
from typing import Optional
import os
import subprocess
import github_tools
import gitlab_tools


def get_review_tools():
    """
    Get the list of review tools based on the platform.
    """
    platform = os.environ.get("PLATFORM")
    if platform == "github":
        return [
            github_tools.get_details,
            github_tools.get_commits_details,
            github_tools.get_changed_files,
            github_tools.get_diffs,
            get_file_contents,
            github_tools.get_comments,
            github_tools.post_comment,
            github_tools.post_review,
        ]
    elif platform == "gitlab":
        return [
            gitlab_tools.get_details,
            gitlab_tools.get_commits_details,
            gitlab_tools.get_changed_files,
            gitlab_tools.get_diffs,
            get_file_contents,
            gitlab_tools.get_comments,
            gitlab_tools.post_comment,
            gitlab_tools.post_review,
        ]
    else:
        # TODO(#31): implement tools for testing platform
        return []


def get_file_contents(file_name: str) -> str:
    """
    Get the current contents of the given file, with line numbers.
    """
    full_path = os.path.join(os.getcwd(), file_name)
    print("full path:", full_path)
    file_exists = os.path.exists(full_path)
    print("exists:", file_exists)
    if not file_exists:
        return "FILE DOES NOT EXIST"

    # Check if it's a text file
    try:
        result = subprocess.run(
            ["file", "-b", "--mime-type", full_path],
            capture_output=True,
            text=True,
            check=True,
        )
        mime_type = result.stdout.strip()

        if not mime_type.startswith("text/"):
            return f"FILE HAS UNSUPPORTED MIME TYPE: {mime_type}"

        # Check line count
        with open(full_path, "r") as f:
            lines = f.readlines()

        if len(lines) >= 1000:
            return f"FILE IS TOO BIG: {len(lines)} lines"

        # Read file content using batcat so it includes line numbers
        batcat_result = subprocess.run(
            [
                "batcat",
                "--style=numbers,plain",
                "--decorations=always",
                full_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return batcat_result.stdout

    except Exception:
        return "ERROR READING FILE"


class ToolsContext:
    def __init__(self):
        self.results = []

    def before_tool_call(
        self, tool: Optional[llm.Tool], tool_call: llm.ToolCall
    ):
        """
        Callback function called before a tool is executed.
        """
        tool_name = tool.name if tool else "unknown"
        print(f"Calling tool {tool_name} with arguments {tool_call.arguments}")

    def after_tool_call(
        self,
        tool: llm.Tool,
        tool_call: llm.ToolCall,
        tool_result: llm.ToolResult,
    ):
        """
        Callback function called after a tool is executed.
        """
        if len(tool_result.output) < 100:
            print(
                f"Called tool {tool.name} with arguments {tool_call.arguments}, response: {tool_result.output}"
            )
        else:
            print(
                f"Called tool {tool.name} with arguments {tool_call.arguments}, response length: {len(tool_result.output)}"
            )
        self.results.append(
            {
                "name": tool.name,
                "arguments": tool_call.arguments,
                "output": tool_result.output,
            }
        )
