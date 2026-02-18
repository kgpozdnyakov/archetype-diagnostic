from __future__ import annotations

from typing import Any

from sqlalchemy import select

from core.scoring import ARCHETYPES
from db.database import SessionLocal
from db.models import Option, Question, QuestionType, TestStatus, TestVersion

VERSION_NAME = "v2-ru-grouped"

DRIVERS = [
    "Роль и границы",
    "Скорость изменений",
    "Надежность",
    "Безопасность и комплаенс",
    "Экономика платформы",
]

ARCHETYPE_LABELS = {
    "Operator": "Operator (Оператор)",
    "InternalOutsourcer": "InternalOutsourcer (Внутренний аутсорсер)",
    "FeatureFactory": "FeatureFactory (Фабрика фич)",
    "ProductFactory": "ProductFactory (Продуктовая фабрика)",
    "PlatformHouse": "PlatformHouse (Платформенный дом)",
    "CompetenceCenter": "CompetenceCenter (Центр компетенций)",
    "DigitalTransformationCenter": "DigitalTransformationCenter (Центр цифровой трансформации)",
    "CaptiveExporter": "CaptiveExporter (Кэптив-экспортер)",
}

SECONDARY = {
    "Operator": "PlatformHouse",
    "InternalOutsourcer": "CaptiveExporter",
    "FeatureFactory": "ProductFactory",
    "ProductFactory": "FeatureFactory",
    "PlatformHouse": "Operator",
    "CompetenceCenter": "Operator",
    "DigitalTransformationCenter": "ProductFactory",
    "CaptiveExporter": "InternalOutsourcer",
}

OPPOSITE = {
    "Operator": "FeatureFactory",
    "InternalOutsourcer": "ProductFactory",
    "FeatureFactory": "Operator",
    "ProductFactory": "InternalOutsourcer",
    "PlatformHouse": "CaptiveExporter",
    "CompetenceCenter": "FeatureFactory",
    "DigitalTransformationCenter": "InternalOutsourcer",
    "CaptiveExporter": "PlatformHouse",
}


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
    questions: list[dict[str, Any]] = [
        {
            "group_name": "Роль и границы",
            "text": "Где сосредоточена ответственность за бизнес-результат IT?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[0],
            "options": [
                {
                    "text": "В операционном контуре с упором на стабильность",
                    "weights": full_weights("Operator", "CompetenceCenter"),
                },
                {
                    "text": "В продуктовых командах с P&L по направлениям",
                    "weights": full_weights("ProductFactory", "FeatureFactory"),
                },
                {
                    "text": "В платформенной функции, обслуживающей домены",
                    "weights": full_weights("PlatformHouse", "DigitalTransformationCenter"),
                },
            ],
        },
        {
            "group_name": "Роль и границы",
            "text": "Как обычно принимаются решения по изменениям в IT-ландшафте?",
            "type": QuestionType.SINGLE,
            "required": True,
            "driver_tag": DRIVERS[1],
            "options": [
                {
                    "text": "Через единый центр и стандартизированные процессы",
                    "weights": full_weights("CompetenceCenter", "Operator"),
                },
                {
                    "text": "Через автономные команды с высокой скоростью",
                    "weights": full_weights("FeatureFactory", "ProductFactory"),
                },
                {
                    "text": "Через программу трансформации с межфункциональной координацией",
                    "weights": full_weights("DigitalTransformationCenter", "PlatformHouse"),
                },
            ],
        },
        {
            "group_name": "Роль и границы",
            "text": "Насколько четко определены границы сервисов и команд?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[0],
            "scale_primary": "PlatformHouse",
            "scale_secondary": "CompetenceCenter",
        },
        {
            "group_name": "Роль и границы",
            "text": "Насколько критична предсказуемость операций и SLA?",
            "type": QuestionType.SCALE,
            "required": True,
            "driver_tag": DRIVERS[2],
            "scale_primary": "Operator",
            "scale_secondary": "PlatformHouse",
        },
    ]

    for archetype in ARCHETYPES:
        secondary = SECONDARY[archetype]
        opposite = OPPOSITE[archetype]
        label = ARCHETYPE_LABELS[archetype]
        group_name = f"Архетип: {label}"

        questions.append(
            {
                "group_name": group_name,
                "text": f"Насколько вашей организации близок управленческий фокус «{label}»?",
                "type": QuestionType.SCALE,
                "required": True,
                "driver_tag": None,
                "scale_primary": archetype,
                "scale_secondary": secondary,
            }
        )
        questions.append(
            {
                "group_name": group_name,
                "text": f"Какой сценарий лучше описывает вашу организацию в контексте «{label}»?",
                "type": QuestionType.SINGLE,
                "required": True,
                "driver_tag": None,
                "options": [
                    {
                        "text": f"Явный приоритет на модель {label}",
                        "weights": full_weights(archetype, secondary),
                    },
                    {
                        "text": "Сбалансированная модель между текущим и соседним архетипом",
                        "weights": full_weights(secondary, archetype),
                    },
                    {
                        "text": "Фокус на альтернативной организационной модели",
                        "weights": full_weights(opposite, secondary),
                    },
                ],
            }
        )

    return questions


def seed() -> None:
    session = SessionLocal()
    try:
        existing = session.scalar(select(TestVersion.id).where(TestVersion.name == VERSION_NAME))
        if existing is not None:
            print(f"Version {VERSION_NAME} already seeded")
            return

        version = TestVersion(name=VERSION_NAME, status=TestStatus.PUBLISHED)
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
                group_name=q["group_name"],
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
        print(f"Seed completed: {VERSION_NAME}")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
