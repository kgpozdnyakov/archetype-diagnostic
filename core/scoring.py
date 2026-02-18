from __future__ import annotations

from collections.abc import Iterable

ARCHETYPES = [
    "Operator",
    "InternalOutsourcer",
    "FeatureFactory",
    "ProductFactory",
    "PlatformHouse",
    "CompetenceCenter",
    "DigitalTransformationCenter",
    "CaptiveExporter",
]


def sum_weights(weight_sets: Iterable[dict[str, float]]) -> dict[str, float]:
    totals = {a: 0.0 for a in ARCHETYPES}
    for weights in weight_sets:
        for archetype in ARCHETYPES:
            totals[archetype] += float(weights.get(archetype, 0.0))
    return totals


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return {a: 0.0 for a in ARCHETYPES}
    return {a: round((scores.get(a, 0.0) / total) * 100.0, 2) for a in ARCHETYPES}


def top_two(percentages: dict[str, float]) -> list[str]:
    sorted_items = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_items[:2]]
