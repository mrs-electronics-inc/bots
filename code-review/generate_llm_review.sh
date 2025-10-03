#!/bin/bash

# This script generates the LLM review.
echo "Generating LLM review..."

# Use the name expected by llm-openrouter
LLM_OPENROUTER_KEY=OPENROUTER_KEY

# Clean up the responses directory
[ -d ".bots/response" ] && rm -rf ".bots/response"
mkdir .bots/response

# Generate the LLM review using Python script
generate_llm_review.py
