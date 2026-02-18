from __future__ import annotations

import csv
import io
import json
import os
from math import ceil

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

from core.scoring import ARCHETYPES, normalize_scores, sum_weights, top_two
from db import repo
from db.database import SessionLocal
from db.models import QuestionType, TestStatus

load_dotenv()

ADMIN_MODE = os.getenv("ADMIN_MODE", "false").lower() == "true"

DRIVERS = [
    "P&L ownership",
    "Time-to-market",
    "Reliability",
    "Security/Compliance",
    "Cost pressure",
]

st.set_page_config(page_title="Archetype Diagnostic Test", layout="centered")

st.title("Archetype Diagnostic Test")


def render_db_not_ready() -> None:
    st.info("DB not initialized, run seed")
    st.stop()


if "started" not in st.session_state:
    st.session_state.started = False
if "page" not in st.session_state:
    st.session_state.page = 0
if "completed" not in st.session_state:
    st.session_state.completed = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_drivers" not in st.session_state:
    st.session_state.last_drivers = []
if "last_answers" not in st.session_state:
    st.session_state.last_answers = {}
if "last_user_label" not in st.session_state:
    st.session_state.last_user_label = None

with SessionLocal() as session:
    try:
        published_versions = repo.get_published_versions(session)
    except OperationalError:
        render_db_not_ready()

    if not published_versions:
        render_db_not_ready()

    version_options = {f"{v.name} (id={v.id})": v.id for v in published_versions}
    selected_label = st.selectbox("Published version", list(version_options.keys()))
    selected_version_id = version_options[selected_label]

    version = repo.get_published_version(session, selected_version_id)
    if not version:
        render_db_not_ready()
    assert version is not None

    questions = sorted(version.questions, key=lambda q: q.id)

    option_by_id = {opt.id: opt for q in questions for opt in q.options}

    st.write(
        "Answer the questions below. Required questions must be completed before submitting."
    )

    if not st.session_state.started:
        if st.button("Start"):
            st.session_state.started = True
        st.stop()

    page_size = 5
    total_pages = ceil(len(questions) / page_size)
    current_page = min(st.session_state.page, total_pages - 1)

    page_questions = questions[current_page * page_size : (current_page + 1) * page_size]

    st.caption(f"Page {current_page + 1} of {total_pages}")

    for q in page_questions:
        st.subheader(q.text)
        key = f"q_{q.id}"
        if q.type == QuestionType.SINGLE:
            option_ids = [opt.id for opt in q.options]
            st.radio(
                "Select one",
                options=option_ids,
                format_func=lambda oid: option_by_id[oid].text,
                key=key,
                index=None,
            )
        else:
            option_ids = sorted([opt.id for opt in q.options],
                key=lambda oid: option_by_id[oid].value or 0,
            )
            st.radio(
                "Rate 1-5",
                options=option_ids,
                format_func=lambda oid: option_by_id[oid].text,
                key=key,
                index=None,
            )

    col_prev, col_next = st.columns(2)
    if col_prev.button("Previous", disabled=current_page == 0):
        st.session_state.page = max(0, current_page - 1)
        st.rerun()
    if col_next.button("Next", disabled=current_page >= total_pages - 1):
        st.session_state.page = min(total_pages - 1, current_page + 1)
        st.rerun()

    st.divider()
    user_label = st.text_input("User label (optional)")
    comment = st.text_area("Comment (optional)")

    if st.button("Submit"):
        missing = []
        answers: dict[str, dict[str, object]] = {}
        weights_list = []
        drivers = []

        for q in questions:
            selected_option_id = st.session_state.get(f"q_{q.id}")
            if q.required and not selected_option_id:
                missing.append(q.text)
                continue
            if selected_option_id:
                opt = option_by_id[selected_option_id]
                answers[str(q.id)] = {"option_id": opt.id, "value": opt.value}
                weights_list.append(opt.weights)
                if q.driver_tag:
                    drivers.append(q.driver_tag)

        if comment:
            answers["comment"] = {"text": comment, "value": None}

        if missing:
            st.error("Please answer all required questions before submitting.")
            st.stop()

        scores = sum_weights(weights_list)
        percentages = normalize_scores(scores)
        top2 = top_two(percentages)

        result = {"percentages": percentages, "top2": top2}
        drivers = sorted(set(drivers))

        try:
            repo.save_assessment(
                session,
                version_id=selected_version_id,
                user_label=user_label or None,
                answers=answers,
                result=result,
                drivers=drivers,
            )
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

        st.session_state.completed = True
        st.session_state.last_result = result
        st.session_state.last_drivers = drivers
        st.session_state.last_answers = answers
        st.session_state.last_user_label = user_label or None

        st.success("Assessment saved")

    if st.session_state.completed and st.session_state.last_result:
        st.subheader("Results")
        st.bar_chart(st.session_state.last_result["percentages"])
        st.write("Top 2:", ", ".join(st.session_state.last_result["top2"]))
        st.write(
            "Drivers:",
            ", ".join(st.session_state.last_drivers) if st.session_state.last_drivers else "None",
        )

        result_payload = {
            "version_id": selected_version_id,
            "user_label": st.session_state.last_user_label,
            "answers": st.session_state.last_answers,
            "result": st.session_state.last_result,
            "drivers": st.session_state.last_drivers,
        }
        st.download_button(
            "Download result JSON",
            data=json.dumps(result_payload, indent=2),
            file_name="assessment_result.json",
            mime="application/json",
        )

    if ADMIN_MODE:
        st.sidebar.header("Admin")
        section = st.sidebar.selectbox(
            "Section",
            [
                "Questions",
                "Add question",
                "Add option",
                "Edit option weights",
                "Create draft",
                "Publish version",
                "Export stats",
            ],
        )

        if section == "Questions":
            versions = repo.get_versions(session)
            version_map = {f"{v.name} ({v.status})": v.id for v in versions}
            v_label = st.selectbox("Version", list(version_map.keys()))
            v = repo.get_version_with_questions(session, version_map[v_label])
            if v:
                for q in sorted(v.questions, key=lambda q: q.id):
                    st.markdown(f"**Q{q.id}. {q.text}**")
                    st.caption(f"Type: {q.type.value} | Required: {q.required}")
                    if q.driver_tag:
                        st.caption(f"Driver: {q.driver_tag}")
                    for opt in q.options:
                        st.write(f"- {opt.text} | value={opt.value} | weights={opt.weights}")

        if section == "Add question":
            drafts = repo.get_versions_by_status(session, TestStatus.DRAFT)
            if not drafts:
                st.info("No draft versions available")
            else:
                draft_map = {v.name: v.id for v in drafts}
                d_label = st.selectbox("Draft version", list(draft_map.keys()))
                text = st.text_area("Question text")
                qtype = st.selectbox("Type", [QuestionType.SINGLE, QuestionType.SCALE])
                required = st.checkbox("Required", value=True)
                driver_tag = st.selectbox("Driver tag", ["None"] + DRIVERS)
                if st.button("Add question"):
                    repo.add_question(
                        session,
                        version_id=draft_map[d_label],
                        text=text,
                        qtype=qtype,
                        required=required,
                        driver_tag=None if driver_tag == "None" else driver_tag,
                    )
                    st.success("Question added")

        if section == "Add option":
            versions = repo.get_versions(session)
            v_map = {f"{v.name} ({v.status})": v.id for v in versions}
            v_label = st.selectbox("Version", list(v_map.keys()))
            v = repo.get_version_with_questions(session, v_map[v_label])
            if v:
                q_map = {f"Q{q.id}: {q.text}": q.id for q in v.questions}
                q_label = st.selectbox("Question", list(q_map.keys()))
                text = st.text_input("Option text")
                value = st.number_input("Value (optional)", min_value=1, max_value=5, value=1)
                weights = {}
                for archetype in ARCHETYPES:
                    weights[archetype] = st.number_input(
                        f"{archetype} weight", value=0.2, step=0.1
                    )
                if st.button("Add option"):
                    repo.add_option(
                        session,
                        question_id=q_map[q_label],
                        text=text,
                        value=value,
                        weights=weights,
                    )
                    st.success("Option added")

        if section == "Edit option weights":
            versions = repo.get_versions(session)
            v_map = {f"{v.name} ({v.status})": v.id for v in versions}
            v_label = st.selectbox("Version", list(v_map.keys()))
            v = repo.get_version_with_questions(session, v_map[v_label])
            if v:
                option_list = [opt for q in v.questions for opt in q.options]
                o_map = {f"Option {o.id}: {o.text}": o.id for o in option_list}
                if o_map:
                    o_label = st.selectbox("Option", list(o_map.keys()))
                    option_id = o_map[o_label]
                    current = next(o for o in option_list if o.id == option_id)
                    new_weights = {}
                    for archetype in ARCHETYPES:
                        new_weights[archetype] = st.number_input(
                            f"{archetype} weight",
                            value=float(current.weights.get(archetype, 0.0))
                        )
                    if st.button("Update weights"):
                        repo.update_option_weights(session, option_id, new_weights)
                        st.success("Weights updated")
                else:
                    st.info("No options available")

        if section == "Create draft":
            name = st.text_input("Draft name")
            if st.button("Create draft"):
                repo.create_version(session, name=name, status=TestStatus.DRAFT)
                st.success("Draft created")

        if section == "Publish version":
            drafts = repo.get_versions_by_status(session, TestStatus.DRAFT)
            if not drafts:
                st.info("No draft versions available")
            else:
                draft_map = {v.name: v.id for v in drafts}
                d_label = st.selectbox("Draft version", list(draft_map.keys()))
                if st.button("Publish"):
                    repo.publish_version(session, draft_map[d_label])
                    st.success("Version published")

        if section == "Export stats":
            pub = repo.get_versions_by_status(session, TestStatus.PUBLISHED)
            if not pub:
                st.info("No published versions available")
            else:
                pub_map = {v.name: v.id for v in pub}
                p_label = st.selectbox("Published version", list(pub_map.keys()))
                stats = repo.aggregate_stats(session, pub_map[p_label])
                st.write("Count:", stats["count"])
                drivers_text = ", ".join(stats["top_drivers"]) if stats["top_drivers"] else "-"
                st.write("Top drivers:", drivers_text)
                st.bar_chart(stats["avg_percentages"])

                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["archetype", "avg_percentage"])
                for k, v in stats["avg_percentages"].items():
                    writer.writerow([k, round(v, 2)])

                st.download_button(
                    "Download stats CSV",
                    data=csv_buffer.getvalue(),
                    file_name="assessment_stats.csv",
                    mime="text/csv",
                )
                st.download_button(
                    "Download stats JSON",
                    data=json.dumps(stats, indent=2),
                    file_name="assessment_stats.json",
                    mime="application/json",
                )








