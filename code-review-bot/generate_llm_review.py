#!/usr/bin/env python3
"""
Generate LLM code review using the LLM Python API.

Environment Variables:
- REVIEW_MODEL: Model to use (optional, will default to something reasonable and cost-effective)
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
    review_model_id = os.getenv("REVIEW_MODEL", "openrouter/openai/gpt-5-mini")
    cheap_model_id = os.getenv("CHEAP_MODEL", "openrouter/openai/gpt-5-nano")
    platform = os.getenv("PLATFORM", "github")

    # Get review model
    try:
        review_model = llm.get_model(review_model_id)
    except llm.UnknownModelError:
        print(f"Error: Unknown model '{review_model_id}'", file=sys.stderr)
        sys.exit(1)
    # Get cheap model
    try:
        cheap_model = llm.get_model(cheap_model_id)
    except llm.UnknownModelError:
        print(f"Error: Unknown model '{cheap_model_id}'", file=sys.stderr)
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
    try:
        tools_context = ToolsContext()
        response = review_model.chain(
            "Please review my merge request using the provided tools.",
            system=system_prompt,
            tools=get_review_tools(),
            before_call=tools_context.before_tool_call,
            after_call=tools_context.after_tool_call,
        )
        response_text = response.text()
        print("Response length:", len(response_text))
        with open(".bots/response/tool-results.json", "w") as f:
            json.dump(tools_context.results, f)
    except Exception as e:
        print(f"Error generating LLM response: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("Response:", response_text)

    print("Review generated successfully")


if __name__ == "__main__":
    main()
