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


class RateLimiter:
    def __init__(self, limit):
        self._limit = limit
        self._count = 0

    def is_limited(self) -> bool:
        if self._count >= self._limit:
            return True
        self._count += 1
        return False
