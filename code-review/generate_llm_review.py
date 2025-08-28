#!/usr/bin/env python3
import os
import sys
import llm


def main():
    print('models:')
    print(llm.get_models())
    # Get environment variables
    review_model = os.getenv('REVIEW_MODEL', 'openrouter/qwen/qwen3-coder')
    platform = os.getenv('PLATFORM', 'github')

    # Set change name based on platform
    change_name = "pull request" if platform == "github" else "merge request"

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
        with open('.bots/context.md', 'r') as f:
            context = f.read()
    except FileNotFoundError:
        print("Error: Context file not found at .bots/context.md",
              file=sys.stderr)
        sys.exit(1)

    # Define schema
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "raw_change_requests": {"type": "string"},
            "change_requests": {"type": "string"},
            "feedback": {"type": "string"}
        },
        "required": ["summary", "raw_change_requests", "change_requests",
                     "feedback"]
    }

    # Get model and set API key
    try:
        model = llm.get_model(review_model)
        model.key = openrouter_key
    except llm.UnknownModelError:
        print(f"Error: Unknown model '{review_model}'", file=sys.stderr)
        sys.exit(1)

    # Generate response
    try:
        response = model.prompt(
            context,
            system=system_prompt,
            presence_penalty=1.5,
            temperature=1.1,
            schema=schema
        )
        response_text = response.text()
        # TODO: try again if response is empty
    except Exception as e:
        print(f"Error generating LLM response: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # Write response to JSON file
    try:
        with open('.bots/response/review.json', 'w') as f:
            f.write(response_text)
    except Exception as e:
        print(f"Error writing response file: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("Review generated successfully")


if __name__ == '__main__':
    main()
