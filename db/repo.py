from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.scoring import ARCHETYPES
from db.models import Assessment, Option, Question, QuestionType, TestStatus, TestVersion


def get_versions(session: Session) -> list[TestVersion]:
    stmt = select(TestVersion).order_by(TestVersion.created_at.desc())
    return list(session.scalars(stmt))


def get_versions_by_status(session: Session, status: TestStatus) -> list[TestVersion]:
    stmt = (
        select(TestVersion)
        .where(TestVersion.status == status)
        .order_by(TestVersion.created_at.desc())
    )
    return list(session.scalars(stmt))


def get_published_versions(session: Session) -> list[TestVersion]:
    return get_versions_by_status(session, TestStatus.PUBLISHED)


def get_published_version(session: Session, version_id: int) -> TestVersion | None:
    stmt = (
        select(TestVersion)
        .where(TestVersion.id == version_id, TestVersion.status == TestStatus.PUBLISHED)
        .options(selectinload(TestVersion.questions).selectinload(Question.options))
    )
    return session.scalar(stmt)


def get_version_with_questions(session: Session, version_id: int) -> TestVersion | None:
    stmt = (
        select(TestVersion)
        .where(TestVersion.id == version_id)
        .options(selectinload(TestVersion.questions).selectinload(Question.options))
    )
    return session.scalar(stmt)


def create_version(session: Session, name: str, status: TestStatus) -> TestVersion:
    version = TestVersion(name=name, status=status)
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def add_question(
    session: Session,
    version_id: int,
    text: str,
    qtype: QuestionType,
    required: bool,
    driver_tag: str | None,
    group_name: str | None = None,
) -> Question:
    question = Question(
        version_id=version_id,
        text=text,
        type=qtype,
        required=required,
        driver_tag=driver_tag,
        group_name=group_name,
    )
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


def add_option(
    session: Session,
    question_id: int,
    text: str,
    value: int | None,
    weights: dict[str, float],
) -> Option:
    option = Option(question_id=question_id, text=text, value=value, weights=weights)
    session.add(option)
    session.commit()
    session.refresh(option)
    return option


def update_option_weights(session: Session, option_id: int, weights: dict[str, float]) -> Option:
    option = session.get(Option, option_id)
    if not option:
        raise ValueError("Option not found")
    option.weights = weights
    session.commit()
    session.refresh(option)
    return option


def publish_version(session: Session, version_id: int) -> TestVersion:
    version = session.get(TestVersion, version_id)
    if not version:
        raise ValueError("Version not found")
    version.status = TestStatus.PUBLISHED
    session.commit()
    session.refresh(version)
    return version


def save_assessment(
    session: Session,
    version_id: int,
    user_label: str | None,
    answers: dict[str, Any],
    result: dict[str, Any],
    drivers: list[str],
) -> Assessment:
    version = session.get(TestVersion, version_id)
    if not version:
        raise ValueError("Version not found")
    if version.status != TestStatus.PUBLISHED:
        raise ValueError("Assessments can only be saved for published versions")

    assessment = Assessment(
        version_id=version_id,
        user_label=user_label,
        answers=answers,
        result=result,
        drivers=drivers,
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def list_questions(session: Session, version_id: int) -> list[Question]:
    stmt = (
        select(Question)
        .where(Question.version_id == version_id)
        .options(selectinload(Question.options))
        .order_by(Question.id)
    )
    return list(session.scalars(stmt))


def aggregate_stats(session: Session, version_id: int) -> dict[str, Any]:
    stmt = select(Assessment).where(Assessment.version_id == version_id)
    rows = list(session.scalars(stmt))
    count = len(rows)
    if count == 0:
        return {"count": 0, "avg_percentages": {a: 0.0 for a in ARCHETYPES}, "top_drivers": []}

    totals = {a: 0.0 for a in ARCHETYPES}
    driver_counts: dict[str, int] = {}
    for row in rows:
        percentages = row.result.get("percentages", {})
        for archetype in ARCHETYPES:
            totals[archetype] += float(percentages.get(archetype, 0.0))
        for driver in row.drivers:
            driver_counts[driver] = driver_counts.get(driver, 0) + 1

    avg = {k: v / count for k, v in totals.items()}
    top_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "count": count,
        "avg_percentages": avg,
        "top_drivers": [d for d, _ in top_drivers[:5]],
    }
