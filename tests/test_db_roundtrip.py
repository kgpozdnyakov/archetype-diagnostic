from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, QuestionType, TestStatus, TestVersion
from db.repo import add_option, add_question, save_assessment


def test_assessment_roundtrip() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        version = TestVersion(name="v1", status=TestStatus.PUBLISHED)
        session.add(version)
        session.commit()
        session.refresh(version)

        question = add_question(
            session,
            version_id=version.id,
            text="Test question",
            qtype=QuestionType.SINGLE,
            required=True,
            driver_tag=None,
        )
        option = add_option(
            session,
            question_id=question.id,
            text="Option A",
            value=None,
            weights={"Operator": 1.0},
        )

        answers = {str(question.id): {"option_id": option.id, "value": None}}
        result = {"percentages": {"Operator": 100.0}, "top2": ["Operator", "FeatureFactory"]}
        drivers = ["Reliability"]

        assessment = save_assessment(
            session,
            version_id=version.id,
            user_label="tester",
            answers=answers,
            result=result,
            drivers=drivers,
        )

        session.refresh(assessment)
        assert assessment.result["percentages"]["Operator"] == 100.0
        assert assessment.drivers == drivers
