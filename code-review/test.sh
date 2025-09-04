#!/bin/bash
# This directory is set up with a `test.bots` directory that contains pre-built
# context. Run the generate review generator script and check the output.

# Build the current image
docker build . -t code-review-test
# Run the review, pass the OPENROUTER_KEY in from the surrounding environment
# Use jq to format the results
docker run -e OPENROUTER_KEY -v ./test.bots:/repo/.bots/ code-review-test sh -c "generate_llm_review.sh; cat /repo/.bots/response/review.json | jq"

# TODO(#31): how can we grade the result?
