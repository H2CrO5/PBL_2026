# API Specification

Status: reflects the implemented ClassPilot service boundary. See
`shared-integration.md` for metric and security rules.

Two FastAPI services run independently today:

| Service | Base URL (dev) | Docs |
|---|---|---|
| Student Education System API | `http://localhost:8000` | `/docs` |
| Teacher Education System API | `http://localhost:8100` | `/docs` |

Authentication (both services): `POST .../auth/login` returns a `token`; send it as `Authorization: Bearer <token>` on protected endpoints. Tokens are stored in the `sessions` table with an `expires_at`.

Conventions: all bodies are JSON. Types below use JSON/OpenAPI naming. `?` marks nullable/optional.

---

## 1. Student Part API (port 8000)

### Auth — `/auth`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/auth/login` | no | `{student_code, password}` | `{token}` |
| POST | `/auth/logout` | yes | — | `{message}` |
| GET | `/auth/me` | yes | — | `StudentResponse` |

`StudentResponse`: `{id, student_code, name, overall_score, total_answered, total_correct, weak_topics:[str], strong_topics:[str]}`

### Assignments — `/assignments`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/assignments/pending` | yes | — | `[AssignmentResponse]` |
| GET | `/assignments/pending/by-lecture` | yes | — | `[LectureAssignments]` |
| POST | `/assignments/submit` | yes | `{assignment_id, answer_text}` | `SubmissionResponse` |
| POST | `/assignments/{assignment_id}/submissions` | yes | `{answer_text}` or `{answers:[...]}` | `SubmissionResponse` |
| GET | `/assignments/history` | yes | — | `HistoryResponse` |
| GET | `/assignments/history/by-lecture` | yes | — | `[HistoryLectureGroup]` |

- `AssignmentResponse`: `{id, topic, difficulty, question_text, choices:[str]?, question_type, lecture_id?}` — `difficulty` is `easy`/`medium`/`hard`.
- `SubmissionResponse`: `{id, assignment_id, answer_text, is_correct, score, feedback, correct_answer, explanation}` — `is_correct`, `score`, `feedback` are **LLM-generated** (`prompts.GRADING_PROMPT` via Bedrock).
- `HistoryResponse`: `{items:[HistoryItem], total}`

`POST /assignments/submit` is the primary LLM path on the student side (grade → feedback → profile update).
The shared-contract alias performs the same synchronous persisted grading; a
subsequent `GET /submissions/{id}` or `POST /submissions/{id}/grade` returns
that stored result and never grades the answer twice.

### Student history and memory — `/students`, `/submissions`

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/students/{student_id}/assignments/current` | self | current published assignments |
| GET | `/students/{student_id}/history` | self | real submission history |
| GET | `/students/{student_id}/memory` | self | concept mastery with submission evidence |
| GET | `/students/me/memory` | yes | concept mastery for the logged-in student |
| GET | `/submissions/{submission_id}` | owner | persisted grading result |
| POST | `/submissions/{submission_id}/grade` | owner | persisted grading result |

### Dashboard — `/dashboard`

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/dashboard/summary` | yes | `DashboardSummary` |
| GET | `/dashboard/trends` | yes | `TrendsResponse` |

- `DashboardSummary`: `{overall_score, total_answered, total_correct, accuracy, weak_topics:[str], strong_topics:[str], today_answered, today_correct, topic_scores:{str:float}}`
- `TrendsResponse`: `{daily_scores:[{date, score, count}], topic_trends:[{topic, average_score, count}]}`

### Chat (TA Bot) — `/chat`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/chat/message` | yes | `{message}` | `ChatMessageResponse` |
| POST | `/chat` | yes | `{message}` | `ChatMessageResponse` |
| GET | `/chat/history` | yes | — | `ChatHistoryResponse` |

`ChatMessageResponse`: `{id, role, content, sources:[{source, score}]?}` — RAG over FAISS + Bedrock generation. `sources` are retrieval citations.

### Admin (dev/debug DB viewer) — `/admin`

Read-only DB inspection: `/admin/db/students`, `/db/lectures`, `/db/assignments`, `/db/submissions`, `/db/chat_messages`, `/db/stats`. Not part of the product contract; likely removed or role-gated at integration.

### Teacher integration — `/integrations/teacher`

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/integrations/teacher/analytics?external_course_id=...` | `X-Integration-Token` | `TeacherAnalyticsFeed` |
| GET | `/integrations/teacher/assignments/{external_assignment_id}/analytics` | `X-Integration-Token` | real assignment analytics |
| POST | `/integrations/teacher/courses/sync` | `X-Integration-Token` | course/enrollment sync |
| POST | `/integrations/teacher/assignments/publish` | `X-Integration-Token` | idempotent publication |
| POST | `/integrations/teacher/materials/sync` | `X-Integration-Token` | course RAG ingestion |
| POST | `/integrations/teacher/submissions/{id}/override` | `X-Integration-Token` | grade correction |

This service boundary exposes real Student submission aggregates and tightly
scoped Teacher writes. It never exposes password
hashes, login sessions, or correct answers. Seed and synthetic submissions are
excluded from live analytics. The shared `TEACHER_INTEGRATION_TOKEN` must be
configured in both processes; when absent, the endpoint returns 503.

`TeacherAnalyticsFeed` contains `data_source`, `generated_at`, per-student
average/completion/weak/strong topics, recent submissions, recent TA Bot
questions and class score trend, plus per-topic attempt counts and wrong rates.

---

## 2. Teacher Part API (port 8100)

When integration is configured, these endpoints use real Student data. Teacher
Bedrock narration and grounded draft generation are enabled with
`TEACHER_USE_LLM=1`.

### Auth — `/auth`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/auth/login` | no | `{teacher_code, password}` | `{token}` |
| POST | `/auth/logout` | yes | — | `{message}` |
| GET | `/auth/me` | yes | — | `TeacherResponse` `{id, teacher_code, name}` |

### Materials — `/materials`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/materials/lectures` | yes | — | `[LectureResponse]` |
| GET | `/materials` | yes | — | `[MaterialResponse]` |
| POST | `/materials` | yes | `MaterialCreateRequest` | `MaterialResponse` |
| POST | `/materials/upload` | yes | multipart PDF/PPTX/MD/TXT | `MaterialResponse` |
| POST | `/materials/sync-all` | yes | — | ingestion summary |
| POST | `/materials/{material_id}/sync` | yes | — | ingestion result |

- `LectureResponse`: `{id, lecture_number, title, learning_objectives:[str]}`
- `MaterialResponse`: `{id, course_id, lecture_id, lecture_title, title, material_type, ingestion_status, content_preview}`
- `MaterialCreateRequest`: `{course_id, lecture_id, title, material_type, content}`

Integration note: Student Part must not read teacher material files directly; the shared backend ingests these records into the shared RAG/vector pipeline.

### Questions (seeds) — `/questions`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/questions` | yes | — | `[QuestionSeedResponse]` |
| POST | `/questions` | yes | `QuestionSeedCreateRequest` | `QuestionSeedResponse` |
| POST | `/questions/generate` | yes | `QuestionGenerateRequest` | grounded draft seed |
| POST | `/questions/{seed_id}/publish` | yes | target/due date | publication result |
| GET | `/questions/generation-context/{lecture_id}` | yes | — | `GenerationContextResponse` |

- `QuestionSeedCreateRequest`: `{course_id, lecture_id, title, target_concept, seed_type("base"|"required"|"rubric_seed")="base", difficulty("supportive"|"balanced"|"challenging")="balanced", question_text, expected_answer, rubric:[str], notes?}`
- `GenerationContextResponse`: `{course_id, lecture_id, lecture_title, learning_objectives:[str], materials:[{id, title, material_type, ingestion_status}], material_titles:[str], weak_concepts:[str], question_seeds:[QuestionSeedResponse], question_seed_candidates:[QuestionSeedCandidateResponse], readiness_checks:[{name, status("ready"|"warning"|"blocked"), detail}], ready_for_generation:bool, backend_instruction}` — the preview of what the shared backend will consume to generate assignments. `question_seed_candidates` are locally-suggested seeds for teacher review; `readiness_checks` gate handoff.

`seed_type`: `base` (backend may adapt) / `required` (must be represented) / `rubric_seed` (grading guidance). Structured teacher controls live in `notes`: Assessment scope (`practice_only`/`formative_checkpoint`/`exam_relevant`), Variation policy (`allow_variants`/`teacher_review_required`/`do_not_generate_variants`), Teacher priority (`normal`/`high`/`critical`).

### Shared assignment contract — `/assignments`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/assignments/generate` | yes | grounded draft generation with goal, difficulty and optional target students |
| GET | `/assignments` | yes | list reviewed/published assignments |
| POST | `/assignments/{assignment_id}/publish` | yes | idempotently publish to Student |
| GET | `/assignments/{assignment_id}/analytics` | yes | real completion, score, missing-concept and error-pattern analytics |

### Course-scoped compatibility contract — `/courses`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/courses/{course_id}/analytics/class` | yes | class dashboard from real submissions |
| GET | `/courses/{course_id}/assignments` | yes | course assignment list |
| GET | `/courses/{course_id}/materials` | yes | course materials and ingestion status |
| POST | `/courses/{course_id}/materials` | yes | create material and make it available for RAG sync |

### Analytics — `/analytics`

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/analytics/dashboard` | yes | — | `DashboardSummary` |
| GET | `/analytics/evidence` | yes | — | `[EvidenceItem]` |
| POST | `/analytics/lecture-plan` | yes | `{course_id, question_seed_id?}` | `LecturePlanResponse` |

- `DashboardSummary`: `{course_id, course_title, total_students, average_score, completion_rate, weak_concepts:[{concept, wrong_rate, misconception, recommended_focus}], question_seed_count, required_question_count, teacher_actions:[{priority, title, reason, next_step}]}`
- The implemented dashboard also returns `data_source` and `data_updated_at` so
  the UI clearly distinguishes real Student submissions from Teacher demo data.
- `EvidenceItem`: `{concept, confidence, evidence_status, affected_students:[str], related_question_seeds:[str], typical_errors:[str], recommended_action}` — evidence-backed weak-concept view.
- `LecturePlanResponse`: `{weakest_concepts:[str], common_misconceptions:[str], recommended_focus:[str], suggested_activity, opening_activity, review_sequence:[str], in_class_check, follow_up_actions:[str], recommended_seed_titles:[str]}` — grounded LLM narration is used when `TEACHER_USE_LLM=1`, with a deterministic fallback.

### Students (analytics) — `/students`

| Method | Path | Auth | Response |
|---|---|---|---|
| GET | `/students/insights` | yes | `[StudentInsightResponse]` |
| POST | `/students/submissions/{id}/override` | yes | corrected score/feedback | corrected grade |

`StudentInsightResponse`: `{id, student_code, name, average_score, completion_rate, strong_topics:[str], weak_topics:[str], recommended_action}`

When live integration is configured, student insights also include up to ten
recent real submissions with answer text, score, feedback, and timestamp.

### Admin — `/admin/db/stats` (dev only).

---

## 3. Shared-backend compatibility mapping

Per `development-plan.md` and the contract draft in `teacher/STUDENT_SYNC_README.md`, the independent endpoints converge on a role-based shared API.

### Assignment generation contract (draft)

```
POST /backend/assignments/generate
```

Input (draft): `{course_id, lecture_id, student_id, material_ids:[int], question_seed_ids:[int], weak_concepts:[str], student_memory:{weak_topics:[str], strong_topics:[str], recent_scores:[int]}}`

Output (draft): `{assignment_id, student_id, lecture_id, questions:[{question_id, source_seed_id, target_concept, difficulty, question_text, expected_answer, rubric:[str]}]}`

The two local FastAPI services implement the public aliases in this section and
communicate through authenticated integration endpoints. A future single
service can retain these frontend contracts while replacing the internal
service token and two SQLite databases.

### Endpoint convergence

| Current (student) | Shared target |
|---|---|
| `GET /assignments/pending` | `GET /students/{student_id}/assignments/current` (implemented) |
| `POST /assignments/submit` | `POST /assignments/{assignment_id}/submissions` (implemented) |
| `GET /assignments/history` | `GET /students/{student_id}/history` (implemented) |
| `POST /chat/message` | `POST /chat` (implemented) |

| Current (teacher) | Shared target |
|---|---|
| `POST /materials` | `POST /courses/{course_id}/materials` (implemented; explicit sync triggers ingestion) |
| `POST /questions/generate` | `POST /assignments/generate` (implemented) |
| `GET /analytics/dashboard` | `GET /courses/{course_id}/analytics/class` (implemented) |
| `POST /questions/{id}/publish` | `POST /assignments/{id}/publish` (implemented) |

Integration rules (from the plan and sync README):

- Authentication becomes role-based (`student` / `teacher` / `ta`) over one `users` table.
- Student `submissions` become the source data for teacher analytics (no more seeded `student_profiles`).
- Teacher `materials` become the shared RAG knowledge base.
- Teacher `question_seeds` (especially `required`) are preserved as constraints in adaptive generation.
- All LLM calls go through backend services, never from frontend code.

---

## 4. LLM / infrastructure defaults (current)

| Setting | Value | Env override |
|---|---|---|
| LLM model | `anthropic.claude-3-haiku-20240307-v1:0` | `BEDROCK_MODEL_ID` |
| Embedding model | `amazon.titan-embed-text-v2:0` (dim 1024) | `EMBEDDING_MODEL_ID` |
| Region | `us-east-1` | `AWS_REGION` |
| Max tokens / temperature | 2048 / 0.7 | — |
| Auth modes | Bearer token (`AWS_BEARER_TOKEN_BEDROCK`) or boto3 SigV4 | — |

Both services use the same Bedrock authentication and model environment contract.
