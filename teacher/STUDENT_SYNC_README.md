# Teacher Part Development Sync README

This document explains the current Teacher Part development plan for the Student Part team. The Teacher Part is an independent module for now, but it is intentionally shaped so the future shared backend can connect it with the Student Part.

## Current Development Assumption

The project is currently split into two parallel modules:

- Student Part: student dashboard, assignment display, answer submission, grading result, feedback, history, and TA Bot.
- Teacher Part: teacher dashboard, material management, question seed management, class analytics, student analytics, and lecture improvement suggestions.

During this stage, each part can run with its own local database and mock/demo data. After both modules are stable, the shared backend will replace local data stores and unify authentication, RAG, LLM calls, analytics, and assignment generation.

## Teacher Part Responsibility

Teacher Part does not generate the final personalized adaptive assignment.

Teacher Part owns:

- Course material upload and review.
- Lecture-level material organization.
- Teacher-authored base questions.
- Teacher-authored required questions.
- Teacher-authored rubric seeds.
- Class weak-point analysis.
- Individual student insight display.
- Next lecture improvement recommendations.
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
| Slide/book materials | `teacher/materials/` seed files or local UI input | Teacher uploads through shared material API |
| Student profiles | Mock local analytics data | Student Part submissions and learning history |
| Weak concepts | Mock concept metrics | Shared analytics pipeline |
| Base/required questions | Teacher Question Bank UI | Shared question seed service |

### Outputs

| Output | Consumer |
| --- | --- |
| Material metadata and content | Shared RAG pipeline |
| Base question seeds | Shared assignment generation service |
| Required question seeds | Shared assignment generation service |
| Rubric seeds | Shared grading and assignment generation service |
| Weak concepts and misconceptions | Student personalization and teacher dashboard |
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
| `GET` | `/questions/generation-context/{lecture_id}` | Preview backend generation context for a lecture |

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

Future integration expectation:

- Shared backend should combine uploaded materials, question seeds, weak concepts, and student memory.
- Student Part receives final assignments from shared backend, not directly from Teacher Part.
- Required question seeds should be preserved as constraints in adaptive generation.

### Analytics

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/analytics/dashboard` | Class overview, weak concepts, question seed count |
| `POST` | `/analytics/lecture-plan` | Generate next lecture improvement recommendation |

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
4. Teacher adds one new question seed.
5. Teacher confirms generation context contains material titles, weak concepts, and question seeds.
6. Teacher reviews class analytics and lecture recommendation.
7. Teacher reviews individual student insight.

Student-side smoke test can stay independent for now, but should later verify that shared backend can use Teacher Part materials and seeds to produce student-facing assignments.

