"""Turn the AI's per-rule judgements into a score. Pure functions: no database, no AI.

    points possible = High 3, Medium 2, Low 1
    points earned   = Met: all of them, Partially Met: half, Not Met: none
    score           = round(points earned / points possible * 100)
    Pass            = score >= pass threshold AND no critical rule is Not Met
"""

from dataclasses import dataclass, field

from app.schemas import Rule

WEIGHT_POINTS = {"high": 3, "medium": 2, "low": 1}
STATUS_CREDIT = {"met": 1.0, "partially_met": 0.5, "not_met": 0.0}


@dataclass
class CategoryScore:
    category: str
    points_earned: float
    points_possible: int


@dataclass
class ScoreResult:
    score: int
    passed: bool
    critical_failures: list[str]  # IDs of critical rules that were Not Met
    points_earned: dict[str, float]  # per rule ID
    points_possible: dict[str, int]  # per rule ID
    categories: list[CategoryScore] = field(default_factory=list)


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
    categories: dict[str, CategoryScore] = {}
    for rule in rules:
        possible[rule.id] = WEIGHT_POINTS[rule.weight]
        earned[rule.id] = possible[rule.id] * STATUS_CREDIT[statuses[rule.id]]
        category = categories.setdefault(rule.category, CategoryScore(rule.category, 0, 0))
        category.points_earned += earned[rule.id]
        category.points_possible += possible[rule.id]

    # int(x + 0.5) rounds halves up (Python's round() would turn 82.5 into 82).
    score = int(sum(earned.values()) / sum(possible.values()) * 100 + 0.5)
    critical_failures = [rule.id for rule in rules if rule.critical and statuses[rule.id] == "not_met"]
    return ScoreResult(
        score=score,
        passed=score >= pass_threshold and not critical_failures,
        critical_failures=critical_failures,
        points_earned=earned,
        points_possible=possible,
        categories=list(categories.values()),
    )
