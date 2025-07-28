#!/bin/bash

# This script generates the LLM review.
# It expects the .bots/context.md file to exist.

# Generate the LLM review
# TODO: move the summary to a separate multi-line variable
cat .bots/context.md | llm -m summary-model -s "Summarize this pull/merge request. Please note any concerns in the following areas: security, performances, and best practices. For each concern, please include at least one possible solution." > .bots/summary.md
