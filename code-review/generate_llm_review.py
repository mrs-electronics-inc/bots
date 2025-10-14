#!/usr/bin/env python3
"""
Generate LLM code review using the LLM Python API.

Environment Variables:
- REVIEW_MODEL: Model to use (default: 'openrouter/qwen/qwen3-coder')
- PLATFORM: 'github' or 'gitlab' (default: 'github')

The script reads the system prompt template, substitutes environment variables,
appends repository-specific instructions if available,
and generates a structured review using the specified LLM model.
"""
import json
import os
import sys
import llm
from tools import get_review_tools, ToolsContext

MAX_RETRIES = 3


def main():
    # Get environment variables
    review_model = os.getenv("REVIEW_MODEL", "openrouter/x-ai/grok-code-fast-1")
    platform = os.getenv("PLATFORM", "github")

    # Get model
    try:
        model = llm.get_model(review_model)
    except llm.UnknownModelError:
        print(f"Error: Unknown model '{review_model}'", file=sys.stderr)
        sys.exit(1)

    # Read system prompt template
    try:
        with open("/bots/system-prompts/review.md", "r") as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        print("Error: System prompt template not found", file=sys.stderr)
        sys.exit(1)

    # Substitute environment variables in system prompt
    system_prompt = system_prompt_template.replace("$PLATFORM", platform)

    # Append repo-specific instructions if they exist
    try:
        with open(".bots/instructions.md", "r") as f:
            repo_instructions = f.read()
            system_prompt += "\n\n# Repo-specific Instructions\n\n"
            system_prompt += repo_instructions
    except FileNotFoundError:
        system_prompt += "\n\n# Repo-specific Instructions\n\nNone."

    # Generate response
    response_text = get_response_text(model, system_prompt)

    print("Response:", response_text)

    print("Review generated successfully")


def get_response_text(model, system_prompt):
    try:
        for i in range(MAX_RETRIES):
            tools_context = ToolsContext()
            response = model.chain(
                "Please review my merge request using the provided tools.",
                system=system_prompt,
                tools=get_review_tools(),
                before_call=tools_context.before_tool_call,
                after_call=tools_context.after_tool_call,
            )
            response_text = response.text()
            print("Response length:", len(response_text))
            if len(response_text) > 3:
                with open(".bots/response/tool-results.json", "w") as f:
                    json.dump(f, tools_context.results)
                return response_text
            else:
                print(
                    "Received invalid response:", response_text, file=sys.stderr
                )
    except Exception as e:
        print(f"Error generating LLM response: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
