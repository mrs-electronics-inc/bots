#!/usr/bin/env python3
"""
Generate LLM code review using the LLM Python API.

Environment Variables:
- REVIEW_MODEL: Model to use (default: 'openrouter/qwen/qwen3-coder')
- PLATFORM: 'github' or 'gitlab' (default: 'github')

The script reads the system prompt template, substitutes environment variables,
appends repository-specific instructions if available, reads the context,
and generates a structured review using the specified LLM model.
"""
import os
import sys
import json
import llm
from tools import get_review_tools, before_tool_call, after_tool_call

MAX_RETRIES = 3


def main():
    # Get environment variables
    review_model = os.getenv('REVIEW_MODEL', 'openrouter/x-ai/grok-code-fast-1')
    platform = os.getenv('PLATFORM', 'github')

    # Set change name based on platform
    change_name = "pull request" if platform == "github" else "merge request"

    # Get model
    try:
        model = llm.get_model(review_model)
    except llm.UnknownModelError:
        print(f"Error: Unknown model '{review_model}'", file=sys.stderr)
        sys.exit(1)

    # Read system prompt template
    try:
        with open('/bots/system-prompts/review.md', 'r') as f:
            system_prompt_template = f.read()
    except FileNotFoundError:
        print("Error: System prompt template not found", file=sys.stderr)
        sys.exit(1)

    # Substitute environment variables in system prompt
    system_prompt = system_prompt_template.replace(
        '$CHANGE_NAME', change_name).replace(
        '$PLATFORM', platform)

    # Append repo-specific instructions if they exist
    try:
        with open('.bots/instructions.md', 'r') as f:
            repo_instructions = f.read()
            system_prompt += "\n\n# Repo-specific Instructions\n\n"
            system_prompt += repo_instructions
    except FileNotFoundError:
        system_prompt += "\n\n# Repo-specific Instructions\n\nNone."

    # Read context
    try:
        with open('.bots/context.json', 'r') as f:
            context = json.load(f)
    except FileNotFoundError:
        print("Error: Context file not found at .bots/context.json",
              file=sys.stderr)
        sys.exit(1)

    # Generate response
    response_text = get_response_text(model, system_prompt, context)

    # Write response to JSON file
    try:
        with open('.bots/response/review.md', 'w') as f:
            f.write(response_text)
    except Exception as e:
        print(f"Error writing response file: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("Review generated successfully")


def get_response_text(model, system_prompt, context):
    try:
        for i in range(MAX_RETRIES):
            response = model.chain(
                "Please review my merge request.",
                system=system_prompt,
                tools=get_review_tools(context),
                before_call=before_tool_call,
                after_call=after_tool_call,
            )
            response_text = response.text()
            print("Response length:", len(response_text))
            if len(response_text) > 10:
                return response_text
            else:
                print("Received invalid response:",
                      response_text, file=sys.stderr)
    except Exception as e:
        print(f"Error generating LLM response: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
