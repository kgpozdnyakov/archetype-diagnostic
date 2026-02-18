# Archetype Diagnostic Test (MVP)

Streamlit + Postgres MVP for an archetype diagnostic questionnaire. The app stores assessments, calculates archetype scores, and exposes minimal admin tooling.

## Requirements
- Python 3.11+
- Docker + docker compose

## Setup
1. Create `.env` from `.env.example` and adjust if needed.
2. Start Postgres:
   - `docker compose up -d`
3. Apply migrations:
   - `alembic upgrade head`
4. Seed initial published test version:
   - `python -m db.seed`
5. Run the app:
   - `streamlit run app.py`

If the database has not been seeded, the app will show: `DB not initialized, run seed`.

## Environment Variables
- `DATABASE_URL` (required)
  - Example: `postgresql+psycopg://archetype:archetype@localhost:5432/archetype`
- `ADMIN_MODE` (optional)
  - `true` enables admin tools for managing questions, options, and publishing versions.

## Admin Mode
Set `ADMIN_MODE=true` in `.env` and restart Streamlit. Admin tools allow:
- View questions and options
- Add questions
- Add options and set weights
- Publish draft versions
- Export aggregated stats (CSV/JSON)

## Quality
Run locally:
- `python -m ruff check .`
- `python -m mypy .`
- `python -m pytest`
