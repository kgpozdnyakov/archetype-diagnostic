from __future__ import annotations

from core.scoring import normalize_scores, sum_weights, top_two


def test_scoring_normalization_and_top2() -> None:
    weights = [
        {"Operator": 1.0, "ProductFactory": 0.5},
        {"Operator": 0.5},
    ]
    totals = sum_weights(weights)
    percentages = normalize_scores(totals)

    assert round(sum(percentages.values()), 2) == 100.0
    assert percentages["Operator"] == 75.0
    assert percentages["ProductFactory"] == 25.0
    assert top_two(percentages) == ["Operator", "ProductFactory"]
