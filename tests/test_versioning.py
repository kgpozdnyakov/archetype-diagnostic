from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, TestStatus, TestVersion
from db.repo import save_assessment


def test_no_assessment_on_draft_version() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        version = TestVersion(name="draft", status=TestStatus.DRAFT)
        session.add(version)
        session.commit()
        session.refresh(version)

        with pytest.raises(ValueError):
            save_assessment(
                session,
                version_id=version.id,
                user_label=None,
                answers={},
                result={},
                drivers=[],
            )
