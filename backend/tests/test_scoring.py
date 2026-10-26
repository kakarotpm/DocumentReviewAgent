import pytest

from app.schemas import Rule
from app.services.scoring import calculate_score, part_subtotals


def rule(rule_id, weight="medium", critical=False):
    return Rule(id=rule_id, title=rule_id, weight=weight, critical=critical, check="x")


RULES = [
    rule("R-1", "high", critical=True),  # 3 points
    rule("R-2", "medium"),  # 2 points
    rule("R-3", "low"),  # 1 point
]


def test_everything_met_scores_100_and_passes():
    result = calculate_score(RULES, {"R-1": "met", "R-2": "met", "R-3": "met"}, 80)
    assert result.score == 100
    assert result.passed is True
    assert result.critical_failures == []


def test_weights_high_medium_low_are_3_2_1():
    result = calculate_score(RULES, {"R-1": "met", "R-2": "met", "R-3": "met"}, 80)
    assert result.points_possible == {"R-1": 3, "R-2": 2, "R-3": 1}


def test_partially_met_earns_half():
    result = calculate_score(RULES, {"R-1": "met", "R-2": "partially_met", "R-3": "met"}, 80)
    assert result.points_earned["R-2"] == 1.0
    assert result.score == 83  # 5 of 6 points


def test_not_met_earns_nothing():
    result = calculate_score(RULES, {"R-1": "met", "R-2": "not_met", "R-3": "met"}, 80)
    assert result.score == 67  # 4 of 6
    assert result.passed is False  # below threshold


def test_critical_not_met_fails_even_with_high_score():
    rules = [rule("C-1", "low", critical=True)] + [rule(f"R-{i}", "high") for i in range(10)]
    statuses = {"C-1": "not_met", **{f"R-{i}": "met" for i in range(10)}}
    result = calculate_score(rules, statuses, 80)
    assert result.score == 97  # 30 of 31
    assert result.passed is False
    assert result.critical_failures == ["C-1"]


def test_critical_partially_met_does_not_force_fail():
    result = calculate_score(RULES, {"R-1": "partially_met", "R-2": "met", "R-3": "met"}, 75)
    assert result.score == 75  # 4.5 of 6
    assert result.passed is True
    assert result.critical_failures == []


def test_threshold_boundary_is_inclusive():
    assert calculate_score(RULES, {"R-1": "met", "R-2": "partially_met", "R-3": "met"}, 83).passed is True
    assert calculate_score(RULES, {"R-1": "met", "R-2": "partially_met", "R-3": "met"}, 84).passed is False


def test_halves_round_up():
    rules = [rule(f"Q{i}", "low") for i in range(40)]
    statuses = {r.id: "met" for r in rules}
    for i in range(7):
        statuses[f"Q{i}"] = "not_met"  # 33 of 40 points = 82.5%
    assert calculate_score(rules, statuses, 80).score == 83


def test_missing_result_is_an_error():
    with pytest.raises(ValueError, match="No result for rule"):
        calculate_score(RULES, {"R-1": "met"}, 80)


def test_unknown_status_is_an_error():
    with pytest.raises(ValueError, match="Unknown status"):
        calculate_score(RULES, {"R-1": "met", "R-2": "maybe", "R-3": "met"}, 80)


# ---------- Subtotals per part (document / Excel workbook) ----------


def test_subtotal_per_part():
    parts = {"R-1": "document", "R-2": "document", "XL-1": "excel"}
    earned = {"R-1": 3, "R-2": 1, "XL-1": 0}  # document: 4 of 5 = 80; excel: 0 of 3 = 0
    possible = {"R-1": 3, "R-2": 2, "XL-1": 3}
    assert part_subtotals(parts, earned, possible) == {"document": 80, "excel": 0}


def test_subtotal_rounds_halves_up_and_skips_missing_parts():
    # 1.5 of 2 points = 75; 3.5 of 4 would be 87.5 -> 88
    assert part_subtotals({"R-1": "document"}, {"R-1": 1.5}, {"R-1": 2}) == {"document": 75}
    assert part_subtotals({"A": "excel", "B": "excel"}, {"A": 3, "B": 0.5}, {"A": 3, "B": 1}) == {"excel": 88}
