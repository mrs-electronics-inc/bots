import json
import uuid
from typing import Optional
import llm


def before_call(tool: Optional[llm.Tool], tool_call: llm.ToolCall):
    """
    This is called before each tool call. It is useful for debugging.
    """
    print(f"Calling tool {tool.name} with arguments {tool_call.arguments}")


def add_change_request(file_path: str, line_number: int,
                       new_code: Optional[str], review_comment: str,
                       severity: int, is_resolved: bool):
    """
    Add a change request.

    Use this tool for all change requests in the following areas:
    - Best Practices
    - Security
    - Performance
    - Potential Bugs
    - Inconsistencies
    - Incorrect grammar
    - Changes mentioned in the description that seem to be missing from the
      diffs
    - TODO comments added to the diffs that don't include an issue number
    - Anything mentioned in the repo-specific instructions

    Example of correct TODO format (no need to leave feedback on this kind):
    ```diff
    + # TODO(#274) - this diff correctly includes an issue number
    ```

    Example of incorrect TODO format (it should be flagged to the author):
    ```diff
    + # TODO - this diff does not include an issue number, it should be flagged
    ```

    Parameters
    ---
    file_path: str
        The file that needs changed
    start_line_number: int
        The line number of the beginning of the code that should be changed.
    end_line_number: int
        The line number of the end of the code that should be changed.
    new_code: str, optional
        The code suggestion to include in the change request. Use None if there
        is no code suggestion for the change request.
    review_comment: str
        The contents of the change request.
    severity: int
        The severity of the problem, on a scale of 0 to 10.
    is_resolved: boolean
        Indicates if the change has already been applied.
    """
    change_id = str(uuid.uuid4())
    with open(f'.bots/response/change_requests/{change_id}.json', 'w') as f:
        json.dump({file_path: file_path, line_number: line_number,
                  new_code: new_code, review_comment: review_comment,
                  severity: severity, is_resolved: is_resolved}, f)
