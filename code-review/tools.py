from typing import Optional
import llm


def before_call(tool: Optional[llm.Tool], tool_call: llm.ToolCall):
    """
    This is called before each tool call. It is useful for debugging.
    """
    print(f"Calling tool {tool.name} with arguments {tool_call.arguments}")


# TODO: add tools once they are supported by llm-openrouter
