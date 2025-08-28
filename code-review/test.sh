#!/bin/bash
# This directory is set up with a `test.bots` directory that contains pre-built
# context. Run the generate review generator script and check the output.

# Build the current image
docker build . -t code-review-test
# Run the review, pass the OPENROUTER_KEY in from the surrounding environment
docker run -e OPENROUTER_KEY -v ./test.bots:/repo/.bots/ code-review-test generate_llm_review.sh
# Output the result
cat test.bots/response/review.md
# TODO(#31): how can we grade the result?
