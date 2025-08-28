#!/usr/bin/env python3
"""
Generate LLM code review using the LLM Python API.

Input Files:
- /bots/system-prompts/review.md: System prompt template with placeholders
- .bots/instructions.md: Repository-specific instructions (optional)
- .bots/context.json: Context information about the code changes to review

Output Files:
- .bots/response/review.json: Generated review in JSON format with fields:
  - summary: Summary of changes
  - raw_change_requests: Raw change requests
  - change_requests: Formatted change requests
  - feedback: Overall feedback

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

MAX_RETRIES = 3


def main():
    # Get environment variables
    review_model = os.getenv('REVIEW_MODEL', 'openrouter/qwen/qwen3-coder')
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
            context_data = json.load(f)
        
        # Format context for LLM
        context = format_context(context_data)
    except FileNotFoundError:
        print("Error: Context file not found at .bots/context.json",
              file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing context JSON: {e}", file=sys.stderr)
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

    # Generate response
    response_text = get_response_text(model, system_prompt, context, schema)

    # Write response to JSON file
    try:
        with open('.bots/response/review.json', 'w') as f:
            f.write(response_text)
    except Exception as e:
        print(f"Error writing response file: {str(e)}", file=sys.stderr)
        sys.exit(1)

    print("Review generated successfully")


def format_context(context_data):
    """Format context data for LLM consumption."""
    context_parts = []
    
    # Add details
    if 'details' in context_data:
        context_parts.append("\n\n===== BEGIN CONTEXT: details =====\n\n")
        context_parts.append(context_data['details'])
        context_parts.append("\n\n===== END CONTEXT: details =====\n\n")
    
    # Add diffs
    if 'diffs' in context_data:
        context_parts.append("\n\n===== BEGIN CONTEXT: diffs =====\n\n")
        context_parts.append(context_data['diffs'])
        context_parts.append("\n\n===== END CONTEXT: diffs =====\n\n")
    
    # Add comments
    if 'comments' in context_data:
        context_parts.append("\n\n===== BEGIN CONTEXT: comments =====\n\n")
        context_parts.append(context_data['comments'])
        context_parts.append("\n\n===== END CONTEXT: comments =====\n\n")
    
    # Add file contents
    if 'file_contents' in context_data:
        for file_path, content in context_data['file_contents'].items():
            context_parts.append(f"\n\n===== BEGIN FILE: {file_path} =====\n\n")
            context_parts.append(content)
            context_parts.append(f"\n\n===== END FILE: {file_path} =====\n\n")
    
    return ''.join(context_parts)


def get_response_text(model, system_prompt, context, schema):
    try:
        for i in range(MAX_RETRIES):
            response = model.prompt(
                context,
                system=system_prompt,
                presence_penalty=1.5,
                temperature=1.1,
                schema=schema
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
