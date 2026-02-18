from __future__ import annotations

from typing import TypedDict


class AssessmentResult(TypedDict):
    percentages: dict[str, float]
    top2: list[str]
