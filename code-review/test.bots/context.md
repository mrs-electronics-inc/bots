

===== BEGIN CONTEXT: details =====


title:	feat: improve bot response reliability
state:	DRAFT
author:	Pertempto
labels:	
assignees:	
reviewers:	
projects:	
milestone:	
number:	37
url:	https://github.com/mrs-electronics-inc/bots/pull/37
additions:	112
deletions:	38
auto-merge:	disabled
--
Resolves #35 

## Changes

- [x] Use Python API
- [ ] Retry when response is empty


===== END CONTEXT: details =====




===== BEGIN CONTEXT: diffs =====


diff --git a/.github/workflows/code-review.yaml b/.github/workflows/code-review.yaml
index ad251fd..bd2e4ea 100644
--- a/.github/workflows/code-review.yaml
+++ b/.github/workflows/code-review.yaml
@@ -8,7 +8,7 @@ jobs:
   run_code_review_bot:
     runs-on: ubuntu-latest
     container:
-      image: ghcr.io/mrs-electronics-inc/bots/code-review:0.10.0-rc1
+      image: ghcr.io/mrs-electronics-inc/bots/code-review:0.10.0-rc3
       volumes:
         - ${{ github.workspace }}:/repo
     defaults:
@@ -25,3 +25,10 @@ jobs:
           GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
           PULL_REQUEST_NUMBER: ${{ github.event.pull_request.number }}
         run: github_code_review.sh
+      - name: Upload artifact including hidden files
+        uses: actions/upload-artifact@v4
+        with:
+          name: bots-directory
+          path: .bots/
+          include-hidden-files: true
+
diff --git a/code-review/Dockerfile b/code-review/Dockerfile
index db06f58..58034ef 100644
--- a/code-review/Dockerfile
+++ b/code-review/Dockerfile
@@ -9,7 +9,7 @@ RUN apt update \
 # Install UV packages and tools
 ENV PATH="/root/.local/bin:${PATH}" 
 RUN python -m pip install uv \
-    && uv pip install --system python-gitlab \
+    && uv pip install --system python-gitlab llm \
     && uv tool install --force --python python3.12 --with pip aider-chat@latest \
     && uv tool install llm
 
@@ -37,6 +37,7 @@ COPY gitlab_code_review.sh /bin
 COPY github_code_review.sh /bin
 COPY collect_context.sh /bin
 COPY generate_llm_review.sh /bin
+COPY generate_llm_review.py /bin
 COPY post_gitlab_review_comment.py /bin
 COPY system-prompts /bots/system-prompts
 
diff --git a/code-review/generate_llm_review.py b/code-review/generate_llm_review.py
new file mode 100755
index 0000000..4e7cb7a
--- /dev/null
+++ b/code-review/generate_llm_review.py
@@ -0,0 +1,100 @@
+#!/usr/bin/env python3
+import os
+import sys
+import llm
+
+
+def main():
+    # Get environment variables
+    review_model = os.getenv('REVIEW_MODEL', 'openrouter/qwen/qwen3-coder')
+    openrouter_key = os.getenv('OPENROUTER_KEY')
+    platform = os.getenv('PLATFORM', 'github')
+
+    if not openrouter_key:
+        print("Error: OPENROUTER_KEY environment variable not set",
+              file=sys.stderr)
+        sys.exit(1)
+
+    # Set change name based on platform
+    change_name = "pull request" if platform == "github" else "merge request"
+
+    # Read system prompt template
+    try:
+        with open('/bots/system-prompts/review.md', 'r') as f:
+            system_prompt_template = f.read()
+    except FileNotFoundError:
+        print("Error: System prompt template not found", file=sys.stderr)
+        sys.exit(1)
+
+    # Substitute environment variables in system prompt
+    system_prompt = system_prompt_template.replace(
+        '$CHANGE_NAME', change_name).replace(
+        '$PLATFORM', platform)
+
+    # Append repo-specific instructions if they exist
+    try:
+        with open('.bots/instructions.md', 'r') as f:
+            repo_instructions = f.read()
+            system_prompt += "\n\n# Repo-specific Instructions\n\n"
+            system_prompt += repo_instructions
+    except FileNotFoundError:
+        system_prompt += "\n\n# Repo-specific Instructions\n\nNone."
+
+    # Read context
+    try:
+        with open('.bots/context.md', 'r') as f:
+            context = f.read()
+    except FileNotFoundError:
+        print("Error: Context file not found at .bots/context.md",
+              file=sys.stderr)
+        sys.exit(1)
+
+    # Define schema
+    schema = {
+        "type": "object",
+        "properties": {
+            "summary": {"type": "string"},
+            "raw_change_requests": {"type": "string"},
+            "change_requests": {"type": "string"},
+            "feedback": {"type": "string"}
+        },
+        "required": ["summary", "raw_change_requests", "change_requests",
+                     "feedback"]
+    }
+
+    # Get model and set API key
+    try:
+        model = llm.get_model(review_model)
+        model.key = openrouter_key
+    except llm.UnknownModelError:
+        print(f"Error: Unknown model '{review_model}'", file=sys.stderr)
+        sys.exit(1)
+
+    # Generate response
+    try:
+        response = model.prompt(
+            context,
+            system=system_prompt,
+            presence_penalty=1.5,
+            temperature=1.1,
+            schema=schema
+        )
+        response_text = response.text()
+        # TODO: try again if response is empty
+    except Exception as e:
+        print(f"Error generating LLM response: {str(e)}", file=sys.stderr)
+        sys.exit(1)
+
+    # Write response to JSON file
+    try:
+        with open('.bots/response/review.json', 'w') as f:
+            f.write(response_text)
+    except Exception as e:
+        print(f"Error writing response file: {str(e)}", file=sys.stderr)
+        sys.exit(1)
+
+    print("Review generated successfully")
+
+
+if __name__ == '__main__':
+    main()
diff --git a/code-review/generate_llm_review.sh b/code-review/generate_llm_review.sh
index 50774a6..5c31ebb 100755
--- a/code-review/generate_llm_review.sh
+++ b/code-review/generate_llm_review.sh
@@ -4,35 +4,12 @@
 # It expects the .bots/context.md file to exist.
 echo "Generating LLM review..."
 
-REVIEW_MODEL=openrouter/qwen/qwen3-coder
-export CHANGE_NAME=$([ "$PLATFORM" = "github" ] && echo "pull request" || echo "merge request")
-envsubst < /bots/system-prompts/review.md > .bots/system-prompt.md
-
-# Include .bots/instructions.md at the end of the system prompt if it exists
-echo $'\n\n# Repo-specific Instructions\n\n' >> .bots/system-prompt.md
-if [[ -f .bots/instructions.md ]]; then
-    cat .bots/instructions.md >> .bots/system-prompt.md
-else
-    echo 'None.' >> .bots/system-prompt.md
-fi
-
-# Read the system prompt while preserving newlines
-SYSTEM_PROMPT=$(cat .bots/system-prompt.md)
-
-SCHEMA="summary string, raw_change_requests string, change_requests string, feedback string"
-
-
-# This shouldn't be necessary, but without it the `llm` tool won't
-# recognize openrouter models.
-# https://github.com/simonw/llm-openrouter/issues/34
-llm keys set openrouter --value "$OPENROUTER_KEY"
-
 # Clean up the responses directory
 [ -d ".bots/response" ] && rm -rf ".bots/response"
 mkdir .bots/response
 
-# Generate the LLM review
-cat .bots/context.md | llm -m $REVIEW_MODEL -o presence_penalty 1.5 -o temperature 1.1 -s "$SYSTEM_PROMPT" --schema "$SCHEMA" > .bots/response/review.json
+# Generate the LLM review using Python script
+generate_llm_review.py
 
 ls -lah .bots/response/review.json
 
@@ -54,16 +31,5 @@ fi
 echo "## Overall Feedback" >> .bots/response/review.md
 cat .bots/response/review.json | jq -r ".feedback" >> .bots/response/review.md
 echo -e "\n\n" >> .bots/response/review.md
-
-# These are for debugging
-echo "================================"
-echo -e "System Prompt:\n$SYSTEM_PROMPT"
-echo "================================"
-echo -e "Context:\n$(cat .bots/context.md)"
-echo "================================"
-echo -e "Review JSON:\n$(cat .bots/response/review.json)"
-echo "================================"
-echo -e "Review Markdown:\n$(cat .bots/response/review.md)"
-echo "================================"
  
 # TODO(#15): respond to comments and pipe to .bots/response/comments.md


===== END CONTEXT: diffs =====




===== BEGIN CONTEXT: comments =====


{
  "username": "github-actions[bot]",
  "timestamp": "2025-08-28T17:01:33Z",
  "body": "## Overall Feedback\n\n\n\n",
  "id": 3234266659
}


===== END CONTEXT: comments =====


===== BEGIN FILE: .github/workflows/code-review.yaml =====
name: Code Review Bot

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  run_code_review_bot:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/mrs-electronics-inc/bots/code-review:0.10.0-rc3
      volumes:
        - ${{ github.workspace }}:/repo
    defaults:
      run:
        working-directory: /repo
    permissions:
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Run Code Review Bot
        env:
          OPENROUTER_KEY: ${{ secrets.API_KEY_CODE_REVIEW_BOT }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PULL_REQUEST_NUMBER: ${{ github.event.pull_request.number }}
        run: github_code_review.sh
      - name: Upload artifact including hidden files
        uses: actions/upload-artifact@v4
        with:
          name: bots-directory
          path: .bots/
          include-hidden-files: true

===== END FILE: .github/workflows/code-review.yaml =====
===== BEGIN FILE: code-review/Dockerfile =====
FROM python:3.12-slim

SHELL ["/bin/bash", "-c"]

# Install core packages
RUN apt update \
    && apt install -y git wget gpg curl jq gettext file
 
# Install UV packages and tools
ENV PATH="/root/.local/bin:${PATH}" 
RUN python -m pip install uv \
    && uv pip install --system python-gitlab llm \
    && uv tool install --force --python python3.12 --with pip aider-chat@latest \
    && uv tool install llm

# Set up llm tool for openrouter
RUN llm install llm-openrouter

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update && apt install -y gh;

# Install GitLab CLI
RUN wget https://gitlab.com/gitlab-org/cli/-/releases/v1.65.0/downloads/glab_1.65.0_linux_amd64.deb \
    && dpkg -i glab_1.65.0_linux_amd64.deb

# Clean up to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# This is where the git repo will be mounted.
WORKDIR /repo
RUN git config --global --add safe.directory /repo

# Add scripts
COPY gitlab_code_review.sh /bin
COPY github_code_review.sh /bin
COPY collect_context.sh /bin
COPY generate_llm_review.sh /bin
COPY generate_llm_review.py /bin
COPY post_gitlab_review_comment.py /bin
COPY system-prompts /bots/system-prompts

CMD ["/bin/bash"]
===== END FILE: code-review/Dockerfile =====
===== BEGIN FILE: code-review/generate_llm_review.py =====
#!/usr/bin/env python3
import os
import sys
import llm


def main():
    # Get environment variables
    review_model = os.getenv('REVIEW_MODEL', 'openrouter/qwen/qwen3-coder')
    openrouter_key = os.getenv('OPENROUTER_KEY')
    platform = os.getenv('PLATFORM', 'github')

    if not openrouter_key:
        print("Error: OPENROUTER_KEY environment variable not set",
              file=sys.stderr)
        sys.exit(1)

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
===== END FILE: code-review/generate_llm_review.py =====
===== BEGIN FILE: code-review/generate_llm_review.sh =====
#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.
echo "Generating LLM review..."

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review using Python script
generate_llm_review.py

ls -lah .bots/response/review.json

# Add the change requests, if necessary
if [ "$(cat .bots/response/review.json | jq -r '.change_requests')" != "" ]; then
    echo "# Changes Requested" >> .bots/response/review.md
    cat .bots/response/review.json | jq -r ".change_requests" >> .bots/response/review.md
    echo -e "\n\n" >> .bots/response/review.md
fi

# Add the summary, if necessary
if [ "$(cat .bots/response/review.json | jq -r '.summary')" != "" ]; then
    echo "## Summary of Changes" >> .bots/response/review.md
    cat .bots/response/review.json | jq -r ".summary" >> .bots/response/review.md
    echo -e "\n\n" >> .bots/response/review.md
fi

# Add the overall feedback
echo "## Overall Feedback" >> .bots/response/review.md
cat .bots/response/review.json | jq -r ".feedback" >> .bots/response/review.md
echo -e "\n\n" >> .bots/response/review.md
 
# TODO(#15): respond to comments and pipe to .bots/response/comments.md
===== END FILE: code-review/generate_llm_review.sh =====
