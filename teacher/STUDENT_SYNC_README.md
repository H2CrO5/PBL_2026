# Teacher Part Development Sync README

This document explains the current Teacher Part development plan for the Student Part team. The Teacher Part is an independent module for now, but it is intentionally shaped so the future shared backend can connect it with the Student Part.

## Current Development Assumption

The project is currently split into two parallel modules:

- Student Part: student dashboard, assignment display, answer submission, grading result, feedback, history, and TA Bot.
- Teacher Part: teacher dashboard, material management, question seed management, class analytics, student analytics, and lecture improvement suggestions.

During this stage, each part can run with its own local database and mock/demo data. After both modules are stable, the shared backend will replace local data stores and unify authentication, RAG, LLM calls, analytics, and assignment generation.

## Implemented Live Submission Bridge

The first safe integration increment is now available without sharing SQLite
files directly:

```text
Student real submission
-> Student GET /integrations/teacher/analytics
-> Teacher analytics/student endpoints
-> existing Teacher Dashboard, Analytics, and Students views
```

Configure both applications with the same `TEACHER_INTEGRATION_TOKEN` and set
`STUDENT_API_BASE_URL` for the Teacher process. The endpoint is read-only,
service-authenticated, excludes seed/synthetic submissions, and does not expose
credentials or correct answers. If integration is configured but unavailable,
Teacher returns 503 instead of silently displaying demo values.

The current Student prototype still represents one implicit course because its
lecture model has no `course_id`. The bridge therefore maps that one Student
course to the authenticated teacher's first course. Adding shared course and
enrollment IDs remains the next shared-backend migration step.

Copy `.env.example` to `.env`; both `student/run.sh` and `teacher/run.sh` load
the shared root `.env` automatically. This bridge is intentionally compatible
with the future shared-backend contract and can later move behind that service
without rewriting either Streamlit UI.

## Product Scope Boundary

The current project starts after instructors have already finished their lecture slides and teaching materials.

Teacher Part does not:

- Generate slide decks.
- Redesign lecture style.
- Decide the lecture narrative or teaching order.
- Replace the instructor's course planning.

Teacher Part does:

- Read completed slides, notes, book sections, or other lecture materials.
- Help structure those materials into concepts, objectives, likely misconceptions, and assessment scope.
- Let teachers review or author base questions, required questions, and rubric seeds.
- Pass structured material context to the future shared backend for RAG, assignment generation, feedback, and analytics.

The intended workflow is:

```text
Instructor completes lecture slide/materials
-> Teacher Part structures completed materials
-> Teacher reviews concepts and question seeds
-> Shared backend uses the verified structure for student-facing assignments and feedback
```

## Teacher Part Responsibility

Teacher Part does not generate the final personalized adaptive assignment.

Teacher Part owns:

- Course material upload and review.
- Lecture-level material organization.
- Post-slide material structuring.
- Learning objective and concept extraction from completed materials.
- Teacher-authored base questions.
- Teacher-authored required questions.
- Teacher-authored rubric seeds.
- Local candidate question seed suggestions for teacher review.
- Shared-backend generation readiness checks.
- Class weak-point analysis.
- Evidence view for weak concepts.
- Teacher action list.
- Individual student insight display.
- Concrete next lecture improvement action plan.
- Generation context preview for future backend integration.

Shared backend later owns:

- RAG indexing over teacher materials.
- LLM-based adaptive assignment generation.
- Student-memory-aware personalization.
- Auto-grading and feedback generation.
- Synchronizing student submissions into teacher analytics.

## Teacher Part Input and Output

### Inputs

| Input | Current Source | Future Source |
| --- | --- | --- |
| Teacher login | Local SQLite seed data | Shared auth service |
| Course and lecture metadata | Local SQLite seed data | Shared course database |
| Completed slide/book materials | `teacher/materials/` seed files or local UI input | Teacher uploads through shared material API |
| Student profiles | Mock local analytics data | Student Part submissions and learning history |
| Weak concepts | Mock concept metrics | Shared analytics pipeline |
| Base/required questions | Teacher Question Bank UI | Shared question seed service |
| Teacher control notes | Question Bank scope / variation / priority controls | Shared assignment-generation constraints |

### Outputs

| Output | Consumer |
| --- | --- |
| Material metadata and content | Shared RAG pipeline |
| Structured lecture profile | Shared RAG and assignment generation services |
| Base question seeds | Shared assignment generation service |
| Required question seeds | Shared assignment generation service |
| Rubric seeds | Shared grading and assignment generation service |
| Generation readiness checks | Teacher approval workflow and shared backend handoff |
| Weak concepts and misconceptions | Student personalization and teacher dashboard |
| Evidence view | Teacher analytics and intervention planning |
| Teacher action list | Teacher dashboard |
| Lecture improvement recommendation | Teacher dashboard |
| Individual student insight | Teacher dashboard and advising workflow |

## Internal Implementation

The Teacher Part is implemented as:

- Backend: FastAPI, SQLAlchemy, SQLite.
- Frontend: Streamlit, Plotly.
- Seed data: two lecture groups with slide-style and reference-style Markdown materials.
- Local smoke flow: deterministic data and local APIs, no external LLM dependency.

Important folders:

```text
teacher/
  api/                 FastAPI app, routers, schemas
  db/                  SQLAlchemy models, DB setup, seed script
  materials/           Demo slide/book materials for two lecture groups
  smoke_tests/         Teacher-side smoke test checklist
  ui/                  Streamlit teacher UI
  README.md            Setup and run instructions
```

## Current Teacher APIs

All endpoints except login require:

```text
Authorization: Bearer <teacher_token>
```

### Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/login` | Teacher login |
| `POST` | `/auth/logout` | Teacher logout |
| `GET` | `/auth/me` | Get current teacher |

Login request:

```json
{
  "teacher_code": "t2024001",
  "password": "demo123"
}
```

### Materials

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/materials/lectures` | List lectures |
| `GET` | `/materials` | List material records |
| `POST` | `/materials` | Add local text material for smoke testing |

Future integration expectation:

- Student Part should not read Teacher Part material files directly.
- Shared backend should ingest Teacher Part material records into the shared RAG/vector pipeline.
- Student TA Bot and assignment generation should retrieve material through the shared backend.

### Question Seeds

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/questions` | List teacher-authored question seeds |
| `POST` | `/questions` | Create a base/required/rubric seed |
| `GET` | `/questions/generation-context/{lecture_id}` | Preview backend generation context for a lecture, including learning objectives, material ids/types/status, weak concepts, question seeds, candidate seeds, and readiness checks |

Create question seed request:

```json
{
  "course_id": 1,
  "lecture_id": 1,
  "title": "Event capacity status",
  "target_concept": "Edge-case handling",
  "seed_type": "required",
  "difficulty": "balanced",
  "question_text": "Given a room capacity and registered student count, return full, available, or overbooked.",
  "expected_answer": "Compare registered count with capacity and handle equality as full.",
  "rubric": [
    "Identifies inputs",
    "Handles equality boundary",
    "Explains available and overbooked cases"
  ],
  "notes": "Required checkpoint for boundary handling."
}
```

`seed_type` values:

- `base`: optional teacher-provided seed that backend can adapt.
- `required`: must be included or represented in generated assignments.
- `rubric_seed`: grading/rubric guidance for generated variants.

Teacher control notes are stored in the current local prototype as structured text in `notes`:

- `Assessment scope`: `practice_only`, `formative_checkpoint`, or `exam_relevant`.
- `Variation policy`: `allow_variants`, `teacher_review_required`, or `do_not_generate_variants`.
- `Teacher priority`: `normal`, `high`, or `critical`.

These should become first-class shared-backend fields during integration.

Future integration expectation:

- Shared backend should combine uploaded materials, question seeds, weak concepts, and student memory.
- Student Part receives final assignments from shared backend, not directly from Teacher Part.
- Required question seeds should be preserved as constraints in adaptive generation.

### Analytics

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/analytics/dashboard` | Class overview, weak concepts, question seed count, teacher action list |
| `GET` | `/analytics/evidence` | Evidence view for weak concepts, affected students, related seeds, and confidence status |
| `POST` | `/analytics/lecture-plan` | Generate concrete next lecture action plan |

Future integration expectation:

- Student submissions should become the source of analytics.
- Teacher Part currently uses mock `ConceptMetric` and `StudentProfile` data.
- Shared backend should update analytics after grading or learning-history updates.

### Student Insights

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/students/insights` | List individual student profiles and recommendations |

Future integration expectation:

- Student Part owns real student activity and answer history.
- Shared backend transforms student history into teacher-visible weak/strong topic summaries.

## Shared Backend Contract Draft

The future shared backend should expose a unified assignment generation service similar to:

```text
POST /backend/assignments/generate
```

Suggested input:

```json
{
  "course_id": 1,
  "lecture_id": 1,
  "student_id": "s2024001",
  "material_ids": [1, 2],
  "question_seed_ids": [1, 2],
  "weak_concepts": ["Edge-case handling", "Problem decomposition"],
  "student_memory": {
    "weak_topics": ["Trace tables"],
    "strong_topics": ["Pseudocode"],
    "recent_scores": [70, 76, 82]
  }
}
```

Suggested output:

```json
{
  "assignment_id": "generated-assignment-id",
  "student_id": "s2024001",
  "lecture_id": 1,
  "questions": [
    {
      "question_id": "q1",
      "source_seed_id": 1,
      "target_concept": "Edge-case handling",
      "difficulty": "balanced",
      "question_text": "Generated or adapted question text",
      "expected_answer": "Expected answer",
      "rubric": ["Criterion 1", "Criterion 2"]
    }
  ]
}
```

This keeps the Student Part focused on assignment display/submission while preserving teacher constraints from the Question Bank.

## Student Part Integration Notes

Student Part should plan to consume these future shared backend outputs:

- Current assignment by student and lecture.
- Submission endpoint with answer payload.
- Grading result with score, correct answer, explanation, and concept-level feedback.
- Learning history and weak-topic updates.
- TA Bot responses grounded in the same teacher materials.

Teacher Part should plan to consume these future shared backend outputs:

- Aggregated concept metrics by course and lecture.
- Per-student weak/strong topic summaries.
- Submission completion and average score.
- Generated assignment metadata for analytics only.

## Smoke Test Alignment

Teacher-side smoke test should validate:

1. Teacher logs in.
2. Teacher reviews two lecture groups and four material files.
3. Teacher reviews existing base/required/rubric question seeds.
4. Teacher reviews candidate question seeds and backend readiness checks.
5. Teacher adds one new question seed with scope, variation, and priority control notes.
6. Teacher confirms generation context contains material ids/types/status, weak concepts, and question seeds.
7. Teacher reviews class analytics, evidence view, teacher action list, and lecture recommendation.
8. Teacher reviews individual student insight.

Student-side smoke test can stay independent for now, but should later verify that shared backend can use Teacher Part materials and seeds to produce student-facing assignments.
