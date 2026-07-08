# Data Model

Status: reverse-engineered from the current independent prototypes, plus a proposed integration target schema. Reflects the code as of commit `337bc65` (teacher analytics workflow expanded).

This document is the source of truth for database schema discussion. Per `development-plan.md`, schema changes must be proposed here **before** implementation.

Scope:

1. Current Student Part schema (as implemented).
2. Current Teacher Part schema (as implemented).
3. Conflicts and duplication between the two.
4. Proposed integration target schema.
5. Proposed evaluation (`eval/`) tables.

---

## 1. Current Student Part schema

Backend: SQLite via SQLAlchemy (`student/db/models.py`). All timestamps are UTC.

### `students`

| Column | Type | Notes |
|---|---|---|
| id | int PK | autoincrement |
| student_code | text | unique, not null |
| name | text | not null |
| password_hash | text | bcrypt |
| overall_score | float | default 0.0 |
| total_answered | int | default 0 |
| total_correct | int | default 0 |
| weak_topics | text | JSON array string, default `"[]"` |
| strong_topics | text | JSON array string, default `"[]"` |
| created_at / updated_at | datetime | |

### `lectures`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| lecture_number | int | not null |
| title | text | not null |
| description | text | nullable |
| lecture_date | datetime | nullable |
| deadline | datetime | nullable |
| created_at | datetime | |

Note: no `course_id`. Student-side lectures are flat (single implicit course).

### `assignments`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | int FK → students.id | not null |
| lecture_id | int FK → lectures.id | nullable |
| topic | text | not null |
| difficulty | text | `easy` / `medium` / `hard` |
| question_text | text | not null |
| choices | text | JSON, nullable (multiple choice) |
| correct_answer | text | not null |
| explanation | text | not null |
| question_type | text | `multiple_choice` / `short_answer` / `code` |
| created_at | datetime | |

Note: assignments are **per student** (personalized/adaptive), not shared question definitions.

### `submissions`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| assignment_id | int FK → assignments.id | not null |
| student_id | int FK → students.id | not null |
| answer_text | text | not null |
| is_correct | bool | not null |
| score | float | LLM-graded |
| feedback | text | LLM-generated |
| submitted_at | datetime | |

### `chat_messages`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | int FK → students.id | not null |
| role | text | `user` / `assistant` |
| content | text | not null |
| sources | text | JSON (RAG citations), nullable |
| created_at | datetime | |

### `sessions`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | int FK → students.id | not null |
| token | text | unique, Bearer token |
| created_at / expires_at | datetime | |

---

## 2. Current Teacher Part schema

Backend: SQLite via SQLAlchemy (`teacher/db/models.py`). Populated with **deterministic seed data** that mimics future shared-backend inputs. The analytics workflow (evidence view, teacher actions, richer lecture plans, seed candidates, readiness checks) is now substantially built out, but it is still **rule-based Python over seed data — no LLM calls** (confirmed: no Bedrock usage anywhere in `teacher/`).

Product scope (per `teacher/STUDENT_SYNC_README.md`): the Teacher Part is a **post-slide** tool. It structures already-completed lecture materials; it does not generate slides or decide teaching narrative.

### `teachers`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| teacher_code | text | unique |
| name | text | |
| password_hash | text | bcrypt |
| created_at | datetime | |

### `sessions`

Same shape as student `sessions`, but FK is `teacher_id → teachers.id`.

### `courses`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| teacher_id | int FK → teachers.id | |
| title | text | |
| term | text | |
| created_at | datetime | |

### `lectures`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| course_id | int FK → courses.id | **has course scope** |
| lecture_number | int | |
| title | text | |
| learning_objectives | text | JSON array string |
| created_at | datetime | |

### `materials`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| course_id | int FK → courses.id | |
| lecture_id | int FK → lectures.id | |
| title | text | |
| material_type | text | `slide` / `book` / `note` |
| source_path | text | nullable |
| content | text | full text |
| ingestion_status | text | default `ready` (future RAG pipeline hook) |
| created_at | datetime | |

### `student_profiles`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| course_id | int FK → courses.id | |
| student_code | text | **not a FK** — string only |
| name | text | |
| average_score | float | |
| completion_rate | float | |
| strong_topics / weak_topics | text | JSON array string |
| recommended_action | text | |
| updated_at | datetime | |

Denormalized analytics mirror of student data. Primary integration seam with the Student Part.

### `concept_metrics`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| course_id | int FK → courses.id | |
| concept | text | |
| wrong_rate | float | |
| misconception | text | |
| recommended_focus | text | |

### `question_seeds`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| course_id | int FK → courses.id | |
| lecture_id | int FK → lectures.id | nullable |
| title | text | |
| target_concept | text | |
| seed_type | text | `base` / `required` / `rubric_seed` |
| difficulty | text | `supportive` / `balanced` / `challenging` |
| question_text | text | |
| expected_answer | text | |
| rubric | text | JSON list |
| notes | text | nullable; carries structured teacher controls (Assessment scope / Variation policy / Teacher priority) |
| created_at | datetime | |

Teacher-authored anchors/constraints for future shared assignment generation.

### `teacher_reports`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| course_id | int FK → courses.id | |
| question_seed_id | int FK → question_seeds.id | nullable |
| weakest_concepts / common_misconceptions / recommended_focus | text | JSON array string |
| suggested_activity | text | rule-generated string (not LLM) |
| created_at | datetime | |

---

## 3. Conflicts and duplication

| # | Issue | Student side | Teacher side | Integration risk |
|---|---|---|---|---|
| C1 | **Student identity duplicated** | `students` (full record + auth) | `student_profiles` (denormalized mirror, `student_code` as plain string) | High — two sources of truth for who a student is |
| C2 | **Lecture scope mismatch** | `lectures` has no `course_id` | `lectures` is course-scoped | Medium — student lectures cannot be attributed to a course/teacher |
| C3 | **`sessions` table split** | `student_id` FK | `teacher_id` FK | Medium — needs one role-aware session/auth model |
| C4 | **Assignment concept split** | `assignments` = per-student generated items | `question_seeds` = teacher-authored anchors | By design; the `POST /backend/assignments/generate` draft (STUDENT_SYNC_README) is the intended bridge, not yet built |
| C5 | **Concept vs topic vocabulary** | free-text `topic`; `weak_topics` JSON | structured `concept` + `wrong_rate` | Medium — no shared concept taxonomy |
| C6 | **Analytics has no live source** | submissions exist | `student_profiles` / `concept_metrics` seeded, not derived | High — core data flow (submissions → analytics) not wired |
| C7 | **Difficulty vocabulary mismatch** | `easy` / `medium` / `hard` | `supportive` / `balanced` / `challenging` | Low/Medium — must unify one difficulty enum before shared generation maps seeds to assignments |

---

## 4. Proposed integration target schema

Goal: one shared database, role-aware auth, submissions as the single source for analytics. Introduce a **shared concept taxonomy** and a **single difficulty enum** so student and teacher vocabularies unify.

Proposed core tables:

- **`users`** — replaces separate `students` / `teachers`. Columns: `id`, `user_code`, `name`, `password_hash`, `role` (`student` / `teacher` / `ta`), timestamps. Resolves C1, C3.
- **`sessions`** — `user_id` FK, `token`, `expires_at`. Role read from `users.role`. Resolves C3.
- **`courses`** — as teacher side today.
- **`enrollments`** — `course_id`, `user_id` (student) join table. Gives every student a course.
- **`lectures`** — course-scoped (adopt teacher shape, add `deadline` from student side). Resolves C2.
- **`materials`** — as teacher side; becomes the shared RAG source.
- **`concepts`** — shared taxonomy: `id`, `course_id`, `name`, `parent_id`. Referenced by assignments and metrics. Resolves C5.
- **`question_seeds`** — teacher-authored, references `concept_id`; adopt one difficulty enum (resolves C7); promote the `notes` teacher controls (scope/variation/priority) to first-class columns.
- **`assignments`** — generated per student; add `source_seed_id` FK → `question_seeds` and `concept_id`. Resolves C4.
- **`submissions`** — unchanged in spirit; single source of truth for analytics.
- **`chat_messages`** — as student side; `user_id` FK.

Derived / materialized (rebuilt from `submissions`, not hand-seeded — resolves C6):

- **`student_mastery`** — replaces `student_profiles`: `user_id`, `course_id`, `average_score`, `completion_rate`, per-concept mastery.
- **`concept_metrics`** — recomputed from submissions grouped by `concept_id`.
- **`teacher_reports`** — LLM-generated (see `evaluation-system-design.md`), not rule-based strings.

Migration approach: keep the two local databases during independent development. Introduce the shared schema behind the API layer first (frontends already call APIs), then backfill: `students` → `users`(student), `student_profiles`/`concept_metrics` become views/jobs over `submissions`.

The shared backend's assignment-generation contract is drafted as `POST /backend/assignments/generate` in `teacher/STUDENT_SYNC_README.md`; see `api-spec.md` §3.

---

## 5. Proposed evaluation (`eval/`) tables

The evaluation subsystem (see `evaluation-system-design.md`) both consumes and produces data. It is also the **source that replaces teacher-side mock data** with realistic synthetic submissions.

- **`eval_personas`** — synthetic student personas: `id`, `name`, `ability_level`, `misconception_profile` (JSON), `prompt_spec`.
- **`eval_runs`** — one evaluation execution: `id`, `target` (`grading` / `generation` / `analytics` / `ta_bot`), `git_sha`, `model_id`, `started_at`, `status`.
- **`eval_cases`** — individual judged items: `run_id` FK, `input` (JSON), `system_output` (JSON), `judge_score` (float), `judge_rationale`, `passed` (bool).
- **`eval_scores`** — aggregate metrics per run: `run_id` FK, `metric` (e.g. `grading_consistency`, `citation_grounding_rate`, `hallucination_rate`), `value`, `threshold`, `passed`.

Synthetic submissions produced by personas can be written into the shared `submissions` table (flagged `source = "synthetic"`) so teacher analytics can run end-to-end before real student traffic exists.
