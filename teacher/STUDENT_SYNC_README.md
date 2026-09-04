# Teacher Part Development Sync README

This document records the Teacher/Student contract. The modules keep independent
local databases but are now connected through authenticated integration APIs.

## Current Development Assumption

The project is currently split into two parallel modules:

- Student Part: student dashboard, assignment display, answer submission, grading result, feedback, history, and TA Bot.
- Teacher Part: teacher dashboard, material management, question seed management, class analytics, student analytics, and lecture improvement suggestions.

Each part can still run in demo mode. When integration is configured, stable
course IDs, RAG materials, published assignments, real analytics, and grade
corrections move through the service boundary.

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
service-authenticated, includes clearly labeled initial seed answers for the
enrolled demo students, excludes synthetic evaluation rows, and does not expose
credentials or correct answers. Seed answers are read-only in Teacher. If integration is configured but unavailable,
Teacher returns 503 instead of silently displaying demo values.

Student now stores explicit courses and enrollments keyed by the Teacher
course's stable `external_key`. Legacy rows are conservatively migrated into a
separate legacy course.

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

The authenticated Student service boundary now owns:

- Course-scoped RAG indexing over teacher materials.
- Receiving reviewed/targeted Teacher assignments.
- Auto-grading, feedback, learning history, and concept mastery.
- Exposing real submission aggregates to Teacher analytics.

Teacher owns the grounded draft-generation review step and publishes only the
approved result. A future single backend may move this ownership internally
without changing the public contracts.

## Teacher Part Input and Output

### Inputs

| Input | Current Source | Future Source |
| --- | --- | --- |
| Teacher login | Local SQLite seed data | Shared auth service |
| Course and lecture metadata | Local SQLite seed data | Shared course database |
| Completed slide/book materials | `teacher/materials/` seed files or local UI input | Teacher uploads through shared material API |
| Student profiles | Real Student integration feed; explicit demo mode only | Shared managed database/analytics service |
| Weak concepts | Real stored grading results | Shared managed analytics pipeline |
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
| `POST` | `/materials/lectures` | Create a lecture for the teacher's course |
| `GET` | `/materials` | List material records |
| `POST` | `/materials` | Add local text material for smoke testing |
| `POST` | `/materials/upload` | Upload and extract a PDF/PPTX/MD/TXT file of up to 20 MB |
| `POST` | `/materials/{material_id}/audience` | Set a material to `student` or `teacher` audience |

Current integration rule:

- Student Part should not read Teacher Part material files directly.
- Teacher sync sends extracted course material through the authenticated
  integration API; Student indexes it with Titan embeddings (lexical fallback
  when embeddings are unavailable).
- Student TA Bot and grading retrieve only course-scoped chunks. Submissions
  themselves travel through normal APIs, never through RAG.
- Teachers explicitly control the material `audience`. Student material lists
  and TA retrieval exclude teacher-only materials, so teacher notes cannot leak
  through either the page or the assistant.
- A material is committed locally before the Student/RAG call. If that call
  fails, the record and a retryable `sync_error` remain visible to the teacher
  instead of the upload appearing to vanish.

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

Implemented local integration:

- Teacher generation combines uploaded materials, question seeds, real weak
  concepts and Student mastery context through Bedrock.
- Student receives only reviewed assignments through the authenticated
  publication endpoint.
- Required seeds remain explicit Teacher constraints.

### Analytics

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/analytics/dashboard` | Class overview, weak concepts, question seed count, teacher action list |
| `GET` | `/analytics/evidence` | Evidence view for weak concepts, affected students, related seeds, and confidence status |
| `POST` | `/analytics/lecture-plan` | Generate concrete next lecture action plan |

Implemented local integration:

- Real Student submissions are the default analytics source and update after
  grading or an audited score override.
- `ConceptMetric` and `StudentProfile` are used only when
  `TEACHER_DEMO_MODE=1` is intentionally enabled.

### Student Insights

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/students/insights` | List individual student profiles and recommendations |

Implemented local integration:

- Student owns real activity, answers, grading, memory and chat history.
- The integration feed transforms that history into Teacher-visible mastery,
  weak/strong topics, submissions and recent TA Bot questions.

## Shared Backend Contract Compatibility

The local services expose shared-compatible assignment routes:

```text
POST /assignments/generate
POST /assignments/{assignment_id}/publish
POST /assignments/{assignment_id}/submissions
GET  /assignments/{assignment_id}/analytics
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

Student Part now consumes these service outputs:

- Current assignment by student and lecture.
- Submission endpoint with answer payload.
- Grading result with score, correct answer, explanation, and concept-level feedback.
- Learning history and weak-topic updates.
- TA Bot responses grounded in the same teacher materials.

Teacher Part now consumes these service outputs:

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

The combined smoke test must additionally sync a Teacher material into Student
RAG, publish a reviewed assignment, submit and grade it as a Student, and verify
the stored result on Teacher class, assignment and individual-student views.
