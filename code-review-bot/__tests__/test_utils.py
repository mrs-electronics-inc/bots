import importlib.util
import pathlib


def load_utils_module():
    # Load the utils.py by path so the tests don't depend on package import name
    utils_path = pathlib.Path(__file__).resolve().parents[1] / "utils.py"
    spec = importlib.util.spec_from_file_location(
        "codereview_utils", str(utils_path)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {utils_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verify_comment_reason_valid():
    utils = load_utils_module()
    assert utils.verify_comment_reason("suggestion") == ""


def test_verify_comment_reason_invalid():
    utils = load_utils_module()
    assert utils.verify_comment_reason("not-a-reason") == "Invalid reason"


def test_is_review_comment_true_review_prefix():
    utils = load_utils_module()
    assert utils.is_review_comment("# Review This looks fine") is True


def test_is_review_comment_true_changes_requested_prefix():
    utils = load_utils_module()
    assert (
        utils.is_review_comment("# Changes Requested Please update X") is True
    )


def test_is_review_comment_false():
    utils = load_utils_module()
    assert utils.is_review_comment("Just a normal comment") is False


def build_valid_review_content():
    return (
        "# Review\n\n"
        "Some intro text.\n\n"
        "## Summary of Changes\n\n"
        "- Changed A to B\n\n"
        "## Overall Feedback\n\n"
        "Looks good overall.\n"
    )


def test_verify_review_content_valid():
    utils = load_utils_module()
    content = build_valid_review_content()
    assert utils.verify_review_content(content) == ""


def test_verify_review_content_missing_prefix():
    utils = load_utils_module()
    content = build_valid_review_content().replace("# Review\n\n", "", 1)
    assert (
        utils.verify_review_content(content)
        == 'Message must start with "# Review" or "# Changes Requested"'
    )


def test_verify_review_content_missing_section():
    utils = load_utils_module()
    # remove the "## Overall Feedback" section entirely
    content = (
        "# Review\n\n" "Intro\n\n" "## Summary of Changes\n\n" "- One change\n"
    )
    assert (
        utils.verify_review_content(content)
        == 'Message must contain exactly one "## Overall Feedback" section'
    )


def test_verify_review_content_duplicate_section():
    utils = load_utils_module()
    # include "## Summary of Changes" twice to trigger duplicate check
    content = (
        "# Review\n\n"
        "Intro\n\n"
        "## Summary of Changes\n\n"
        "- change 1\n\n"
        "## Summary of Changes\n\n"
        "- change 2\n\n"
        "## Overall Feedback\n\n"
        "ok\n"
    )
    assert (
        utils.verify_review_content(content)
        == 'Message must contain exactly one "## Summary of Changes" section'
    )


def test_rate_limit_decorator_enforces_limit_and_preserves_name():
    utils = load_utils_module()

    @utils.rate_limit(limit=2, error="too many")
    def multiply(x):
        return x * 2

    # decorator should preserve function name via functools.wraps
    assert multiply.__name__ == "multiply"

    assert multiply(2) == 4
    assert multiply(3) == 6
    # third call exceeds limit -> returns error dict
    assert multiply(5) == {"error": "too many"}


def test_rate_limit_decorator_isolated_counts():
    utils = load_utils_module()

    @utils.rate_limit(limit=1, error="first limit")
    def a():
        return "a"

    @utils.rate_limit(limit=2, error="second limit")
    def b():
        return "b"

    assert a() == "a"
    assert a() == {"error": "first limit"}

    assert b() == "b"
    assert b() == "b"
    assert b() == {"error": "second limit"}
