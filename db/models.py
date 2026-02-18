from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TestStatus(StrEnum):
    __test__ = False
    DRAFT = "draft"
    PUBLISHED = "published"


class QuestionType(StrEnum):
    SINGLE = "single"
    SCALE = "scale"


class TestVersion(Base):
    __test__ = False
    __tablename__ = "test_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[TestStatus] = mapped_column(
        SAEnum(
            TestStatus,
            values_callable=lambda enum: [e.value for e in enum],
            name="teststatus",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    questions: Mapped[list[Question]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )
    assessments: Mapped[list[Assessment]] = relationship(back_populates="version")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("test_versions.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[QuestionType] = mapped_column(
        SAEnum(
            QuestionType,
            values_callable=lambda enum: [e.value for e in enum],
            name="questiontype",
        ),
        nullable=False,
    )
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    driver_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    version: Mapped[TestVersion] = relationship(back_populates="questions")
    options: Mapped[list[Option]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(300), nullable=False)
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weights: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)

    question: Mapped[Question] = relationship(back_populates="options")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    version_id: Mapped[int] = mapped_column(ForeignKey("test_versions.id"), nullable=False)
    user_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    answers: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    drivers: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    version: Mapped[TestVersion] = relationship(back_populates="assessments")


