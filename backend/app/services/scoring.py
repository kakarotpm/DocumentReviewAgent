"""Turn the AI's per-rule judgements into a score. Pure functions: no database, no AI.

    points possible = High 3, Medium 2, Low 1
    points earned   = Met: all of them, Partially Met: half, Not Met: none
    score           = round(points earned / points possible * 100)
    Pass            = score >= pass threshold AND no critical rule is Not Met

When a review covers both parts (the document and an Excel workbook), there is still one score
and one Pass/Fail for all rules together; each part also gets a subtotal with the same formula.
"""

from dataclasses import dataclass

from app.schemas import Rule

WEIGHT_POINTS = {"high": 3, "medium": 2, "low": 1}
STATUS_CREDIT = {"met": 1.0, "partially_met": 0.5, "not_met": 0.0}


@dataclass
class ScoreResult:
    score: int
    passed: bool
    critical_failures: list[str]  # IDs of critical rules that were Not Met
    points_earned: dict[str, float]  # per rule ID
    points_possible: dict[str, int]  # per rule ID


def percentage(points_earned: list[float], points_possible: list[int]) -> int:
    """round(earned / possible * 100), rounding halves up (Python's round() would turn 82.5 into 82)."""
    return int(sum(points_earned) / sum(points_possible) * 100 + 0.5)


def part_subtotals(parts: dict[str, str], points_earned: dict[str, float], points_possible: dict[str, int]) -> dict[str, int]:
    """A subtotal (0-100) for each part. `parts` maps rule ID to part; parts with no rules are left out."""
    subtotals = {}
    for part in dict.fromkeys(parts.values()):  # each part once, in order
        ids = [rule_id for rule_id, p in parts.items() if p == part]
        subtotals[part] = percentage([points_earned[i] for i in ids], [points_possible[i] for i in ids])
    return subtotals


def calculate_score(rules: list[Rule], statuses: dict[str, str], pass_threshold: int) -> ScoreResult:
    """Score a review. `statuses` maps every rule ID to met / partially_met / not_met."""
    if not rules:
        raise ValueError("Can't score a review with no rules.")
    missing = [rule.id for rule in rules if rule.id not in statuses]
    if missing:
        raise ValueError(f"No result for rule(s): {', '.join(missing)}")
    unknown = {s for s in statuses.values() if s not in STATUS_CREDIT}
    if unknown:
        raise ValueError(f"Unknown status(es): {', '.join(sorted(unknown))}")

    earned: dict[str, float] = {}
    possible: dict[str, int] = {}
    for rule in rules:
        possible[rule.id] = WEIGHT_POINTS[rule.weight]
        earned[rule.id] = possible[rule.id] * STATUS_CREDIT[statuses[rule.id]]

    score = percentage(list(earned.values()), list(possible.values()))
    critical_failures = [rule.id for rule in rules if rule.critical and statuses[rule.id] == "not_met"]
    return ScoreResult(
        score=score,
        passed=score >= pass_threshold and not critical_failures,
        critical_failures=critical_failures,
        points_earned=earned,
        points_possible=possible,
    )
