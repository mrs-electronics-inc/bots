import functools
import json

# Prefixes for review comments
required_prefixes = ["# Review", "# Changes Requested"]
# Reasons to post a comment. We have these to force the bot to justify each
# comment it wants to post.
comment_reasons = ["suggestion", "clarification", "warning", "response"]


def verify_comment_reason(reason: str):
    """
    Verify the comment reason is valid
    """
    if not reason in comment_reasons:
        return "Invalid reason"
    return ""


def is_review_comment(content: str):
    """Check if a comment body is a review comment based on prefix"""
    return any([content.startswith(prefix) for prefix in required_prefixes])


def verify_review_content(content: str):
    """
    Verify the review content is valid.
    Returns an error message if there are issues, or an empty string if there
    are no problems.
    """
    if not is_review_comment(content):
        return 'Message must start with "# Review" or "# Changes Requested"'

    required_sections = ["## Summary of Changes", "## Overall Feedback"]
    for section in required_sections:
        if content.count(section) != 1:
            return f'Message must contain exactly one "{section}" section'
    return ""


def rate_limit_tool(*, limit: int, error: str):
    """
    Decorator that enforces the given rate limit on the decorated function.
    It is intended for rate limiting our tool functions, which return serialized
    JSON objects and run in a single-threaded environment.
    It is NOT designed to be thread-safe. It is designed to be process-local.
    When the limit is hit, it will return a string which serializes
    {"error": error}
    """

    def decorator(func):
        count = 0

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal count

            if count >= limit:
                return json.dumps({"error": error})
            count += 1
            return func(*args, **kwargs)

        return wrapper

    return decorator
