#!/usr/bin/env python3
"""
Shared utilities for posting code review comments on GitHub and GitLab.
"""
import os


# Prefixes used to identify review comments
REVIEW_COMMENT_PREFIXES = [
    '# Changes Requested',
    '## Summary',
    '## Overall Feedback'
]


def read_review_content():
    """Read the review content from .bots/response/review.md"""
    try:
        with open('.bots/response/review.md', 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError("Review file not found at .bots/response/review.md")


def read_response_content():
    """Read the response content from .bots/response/comments.md if it exists"""
    try:
        with open('.bots/response/comments.md', 'r') as f:
            content = f.read().strip()
            if content and content != "No new responses at this time.":
                return content
    except FileNotFoundError:
        pass  # No comments file is fine
    return None


def is_review_comment(body):
    """Check if a comment body is a review comment based on prefixes"""
    return any(body.startswith(prefix) for prefix in REVIEW_COMMENT_PREFIXES)

