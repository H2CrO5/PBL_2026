# Teacher Education System

Teacher Part prototype for the Adaptive Assignment Generation System.

This module follows `docs/development-plan.md`: it runs independently during module development, then can be integrated later with the shared backend, shared database, shared RAG pipeline, and shared AWS resources.

Scope boundary: this module starts after instructors have already prepared lecture slides and materials. It does not generate slide decks or redesign teaching style; it structures completed materials for question seeds, RAG, analytics, and later shared-backend assignment generation.

For Student Part synchronization, see `STUDENT_SYNC_README.md`.

## Features

- Teacher login.
- Material management.
- Post-slide material structuring.
- Class analytics dashboard.
- Teacher action list.
- Evidence view for weak concepts.
- Teacher-authored base and required question seeds.
- Candidate question seed review.
- Shared-backend generation readiness checks.
- Shared-backend generation context preview.
- Weak-point analysis.
- Individual student analysis.
- Concrete next lecture improvement action plan.

## Stack

- Backend: FastAPI / SQLAlchemy / SQLite
- Frontend: Streamlit / Plotly
- AI behavior: deterministic local data that mimics future shared-backend inputs for smoke testing

## Setup

```bash
cd teacher
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m db.seed
```

Demo teacher account:

```text
t2024001 / demo123
```

## Run

```bash
cd teacher
bash run.sh
```

Services:

- Streamlit UI: http://localhost:8601
- FastAPI: http://localhost:8100
- API docs: http://localhost:8100/docs

## Smoke Test Flow

1. Log in as the demo teacher.
2. Open the dashboard and confirm class metrics and weak concepts.
3. Open materials and confirm two lecture groups have slide/book materials.
4. Open Question Bank and review seeded base/required questions.
5. Review generation readiness checks and candidate question seeds.
6. Add one teacher-authored question seed with an expected answer, rubric, and control notes.
7. Confirm generation context includes material ids/types/status, weak concepts, and question seeds.
8. Open analytics, review evidence, and generate next lecture recommendations.
9. Open student analysis and confirm weak topics and recommended actions.
