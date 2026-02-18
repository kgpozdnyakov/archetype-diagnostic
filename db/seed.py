from __future__ import annotations

from typing import Any

from sqlalchemy import select

from core.scoring import ARCHETYPES
from db.database import SessionLocal
from db.models import Option, Question, QuestionType, TestStatus, TestVersion

DRIVERS = [
    "P&L ownership",
    "Time-to-market",
    "Reliability",
    "Security/Compliance",
    "Cost pressure",
]


def full_weights(
    primary: str,
    secondary: str | None = None,
    primary_weight: float = 1.0,
    secondary_weight: float = 0.6,
    base: float = 0.2,
) -> dict[str, float]:
    weights = {a: base for a in ARCHETYPES}
    weights[primary] = primary_weight
    if secondary:
        weights[secondary] = secondary_weight
    return weights


def scale_weights(primary: str, secondary: str | None, value: int) -> dict[str, float]:
    factor = value / 5.0
    return full_weights(
        primary=primary,
        secondary=secondary,
        primary_weight=1.0 * factor,
        secondary_weight=0.6 * factor,
        base=0.1 * factor,
    )


def build_questions() -> list[dict[str, Any]]:
    return [
        {
            "text": "Where is primary P&L ownership?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[0],
            "options": [
                {
                    "text": "In the operations center",
                    "weights": full_weights("Operator", "CompetenceCenter"),
                },
                {
                    "text": "In product teams",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "In the platform organization",
                    "weights": full_weights("PlatformHouse", "DigitalTransformationCenter"),
                },
            ],
        },
        {
            "text": "How frequently do business priorities change?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[1],
            "scale_primary": "FeatureFactory",
            "scale_secondary": "ProductFactory",
        },
        {
            "text": "How critical is service reliability?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[2],
            "scale_primary": "Operator",
            "scale_secondary": "PlatformHouse",
        },
        {
            "text": "Which delivery model dominates?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": None,
            "options": [
                {
                    "text": "Project delivery on demand",
                    "weights": full_weights("InternalOutsourcer", "CompetenceCenter"),
                },
                {
                    "text": "High-velocity feature delivery",
                    "weights": full_weights("FeatureFactory", "ProductFactory"),
                },
                {
                    "text": "Product lines and roadmaps",
                    "weights": full_weights("ProductFactory", "PlatformHouse"),
                },
            ],
        },
        {
            "text": "How do you fund platform investments?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[4],
            "options": [
                {
                    "text": "Minimize cost, outsource where possible",
                    "weights": full_weights("InternalOutsourcer", "CaptiveExporter"),
                },
                {
                    "text": "Invest to scale the platform",
                    "weights": full_weights("PlatformHouse", "Operator"),
                },
                {
                    "text": "Invest selectively for business needs",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
            ],
        },
        {
            "text": "What is the level of regulatory requirements?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[3],
            "scale_primary": "CompetenceCenter",
            "scale_secondary": "Operator",
        },
        {
            "text": "What do you prioritize in hiring?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": None,
            "options": [
                {
                    "text": "Deep expertise and standards",
                    "weights": full_weights("CompetenceCenter", "Operator"),
                },
                {
                    "text": "Speed and flexibility",
                    "weights": full_weights("FeatureFactory", "ProductFactory"),
                },
                {
                    "text": "Global delivery scale",
                    "weights": full_weights("CaptiveExporter", "InternalOutsourcer"),
                },
            ],
        },
        {
            "text": "How do you run transformation initiatives?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": None,
            "options": [
                {
                    "text": "Central transformation office",
                    "weights": full_weights("DigitalTransformationCenter", "Operator"),
                },
                {
                    "text": "Distributed product ownership",
                    "weights": full_weights("ProductFactory", "PlatformHouse"),
                },
                {
                    "text": "Minimal transformation focus",
                    "weights": full_weights("InternalOutsourcer", "Operator"),
                },
            ],
        },
        {
            "text": "How significant is external customer delivery?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "CaptiveExporter",
            "scale_secondary": "PlatformHouse",
        },
        {
            "text": "How fast do you ship new functionality?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[1],
            "scale_primary": "FeatureFactory",
            "scale_secondary": "ProductFactory",
        },
        {
            "text": "How important is architectural standardization?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "CompetenceCenter",
            "scale_secondary": "PlatformHouse",
        },
        {
            "text": "Where are key competencies concentrated?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": None,
            "options": [
                {
                    "text": "Internal center of excellence",
                    "weights": full_weights("CompetenceCenter", "DigitalTransformationCenter"),
                },
                {
                    "text": "Product teams",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "External providers",
                    "weights": full_weights("InternalOutsourcer", "CaptiveExporter"),
                },
            ],
        },
        {
            "text": "How automated are your operations?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[2],
            "scale_primary": "Operator",
            "scale_secondary": "PlatformHouse",
        },
        {
            "text": "How many active product lines do you run?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "ProductFactory",
            "scale_secondary": "FeatureFactory",
        },
        {
            "text": "How do you justify IT spend?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[4],
            "options": [
                {
                    "text": "Cost minimization",
                    "weights": full_weights("InternalOutsourcer", "CaptiveExporter"),
                },
                {
                    "text": "Product profitability",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "Reliability and compliance",
                    "weights": full_weights("Operator", "CompetenceCenter"),
                },
            ],
        },
        {
            "text": "How critical is market responsiveness?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[1],
            "scale_primary": "DigitalTransformationCenter",
            "scale_secondary": "FeatureFactory",
        },
        {
            "text": "Which security approach dominates?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[3],
            "options": [
                {
                    "text": "Centralized security policies",
                    "weights": full_weights("CompetenceCenter", "Operator"),
                },
                {
                    "text": "Shared ownership in teams",
                    "weights": full_weights("ProductFactory", "PlatformHouse"),
                },
                {
                    "text": "Compliance via external standards",
                    "weights": full_weights("CaptiveExporter", "InternalOutsourcer"),
                },
            ],
        },
        {
            "text": "How unified is your platform stack?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "PlatformHouse",
            "scale_secondary": "Operator",
        },
        {
            "text": "Who owns SLA accountability?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[2],
            "options": [
                {
                    "text": "Central operations owner",
                    "weights": full_weights("Operator", "PlatformHouse"),
                },
                {
                    "text": "Product teams",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "Outsourcing with contracts",
                    "weights": full_weights("InternalOutsourcer", "CaptiveExporter"),
                },
            ],
        },
        {
            "text": "How important is global delivery capability?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "CaptiveExporter",
            "scale_secondary": "InternalOutsourcer",
        },
        {
            "text": "How do you develop internal capabilities?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": None,
            "options": [
                {
                    "text": "Center of excellence programs",
                    "weights": full_weights("CompetenceCenter", "DigitalTransformationCenter"),
                },
                {
                    "text": "Product-driven practices",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "Rely on market providers",
                    "weights": full_weights("InternalOutsourcer", "CaptiveExporter"),
                },
            ],
        },
        {
            "text": "How mature is your product management?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "ProductFactory",
            "scale_secondary": "FeatureFactory",
        },
        {
            "text": "How often do you run technology transformations?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": None,
            "scale_primary": "DigitalTransformationCenter",
            "scale_secondary": "PlatformHouse",
        },
        {
            "text": "Where do core platform services live?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": None,
            "options": [
                {
                    "text": "In a single platform layer",
                    "weights": full_weights("PlatformHouse", "Operator"),
                },
                {
                    "text": "Embedded in product verticals",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "Provided by external vendors",
                    "weights": full_weights("InternalOutsourcer", "CaptiveExporter"),
                },
            ],
        },
    ]


def seed() -> None:
    session = SessionLocal()
    try:
        existing = session.scalar(select(TestVersion.id).limit(1))
        if existing is not None:
            print("Database already seeded")
            return

        version = TestVersion(name="v1", status=TestStatus.PUBLISHED)
        session.add(version)
        session.flush()

        questions = build_questions()
        if not (20 <= len(questions) <= 25):
            raise RuntimeError("Seed must create between 20 and 25 questions")

        for q in questions:
            question = Question(
                version_id=version.id,
                text=q["text"],
                type=q["type"],
                required=q["required"],
                driver_tag=q["driver_tag"],
            )
            session.add(question)
            session.flush()

            if q["type"] == QuestionType.SCALE:
                primary = q["scale_primary"]
                secondary = q["scale_secondary"]
                for value in range(1, 6):
                    option = Option(
                        question_id=question.id,
                        text=str(value),
                        value=value,
                        weights=scale_weights(primary, secondary, value),
                    )
                    session.add(option)
            else:
                for opt in q["options"]:
                    option = Option(
                        question_id=question.id,
                        text=opt["text"],
                        value=opt.get("value"),
                        weights=opt["weights"],
                    )
                    session.add(option)

        session.commit()
        print("Seed completed")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
