"""A document's overall status, worked out from its versions' reviews. Pure function, no database.

    In review  - the latest version's review hasn't finished yet
    Error      - the latest version's review failed
    Failed     - the latest version failed
    Passed     - the latest version passed, and no earlier version failed
    Corrected  - the latest version passed, and at least one earlier version failed
"""


def document_status(version_reviews: list[tuple[str, bool | None]]) -> str:
    """`version_reviews` has one (review status, passed) pair per version, oldest first,
    taken from each version's most recent review."""
    if not version_reviews:
        return "In review"
    latest_status, latest_passed = version_reviews[-1]
    if latest_status in ("queued", "processing"):
        return "In review"
    if latest_status == "error":
        return "Error"
    if not latest_passed:
        return "Failed"
    earlier_failed = any(status == "complete" and passed is False for status, passed in version_reviews[:-1])
    return "Corrected" if earlier_failed else "Passed"
