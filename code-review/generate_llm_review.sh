#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.

SUMMARY_MODEL=openrouter/google/gemini-2.5-flash-lite

# This shouldn't be necessary, but without it the `llm` tool won't
# recognize openrouter models.
# https://github.com/simonw/llm-openrouter/issues/34
llm keys set openrouter --value OPENROUTER_KEY

# Generate the LLM review
# TODO: move the summary to a separate multi-line variable
cat .bots/context.md | llm -m $SUMMARY_MODEL -s "Summarize this pull/merge request. Please note any concerns in the following areas: security, performances, and best practices. For each concern, please include at least one possible solution." > .bots/summary.md
