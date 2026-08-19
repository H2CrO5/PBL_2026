# Status and Roadmap

> Update for the ClassPilot integration branch: course-scoped material RAG,
> Teacher-to-Student assignment publication, real-submission analytics, bounded
> retries, and auditable grade correction are now implemented. Sections below
> describe the historical baseline. Remaining deployment work requires the
> university AWS account, identity provider, and retention-policy decisions.

Companion to `development-plan.md`. The plan describes the intended process;
this document records the integrated ClassPilot branch and the remaining
production-deployment decisions.

Related documents:

- `development-plan.md` — phased plan and team allocation.
- `data-model.md` — current and target database schema.
- `api-spec.md` — current and target API contracts.
- `evaluation-system-design.md` — the `eval/` subsystem (cross-cutting quality gate).
- `teacher/STUDENT_SYNC_README.md` — teacher→student integration contract draft.

---

## 1. Current position at a glance

| Part | Plan phase | Real status |
|---|---|---|
| **Student** | Phase 3 (Student Part development) | **Working prototype with live LLM.** Login, adaptive assignments, LLM auto-grading, feedback, dashboard, history, and RAG TA bot all run against AWS Bedrock. |
| **Teacher** | Phase 4 (in progress) | **Rich workflow UI + analytics, now with optional LLM narration.** Evidence view, teacher action list, seed candidates, backend readiness checks, and expanded lecture plans. Numeric facts stay rule-based; the qualitative narration (typical errors, recommended actions, lecture-plan prose) is LLM-generated when `TEACHER_USE_LLM=1`, reusing a teacher-side Bedrock client, with automatic fallback to the rule-based text. Scope is deliberately **post-slide**: structure completed materials, do not generate slides. |
| **Shared backend** | Phase 2 (local integration) | Stable course/material/assignment IDs and authenticated service APIs connect the two local databases. |
| **Docs** | Phase 1 | API, model, integration, setup, safety, and production migration documents are present. |
| **Evaluation** | Cross-cutting | Grading, generation, TA grounding, and analytics gates run offline and in CI. |

Summary: Student and Teacher are connected locally. Teacher materials feed
course-scoped RAG, reviewed questions publish to Student, real submissions drive
analytics, and grade corrections flow back with audit history.

---

## 2. What is done

- **Student**: real Bedrock client with dual auth (Bearer / SigV4), LLM grading (`GRADING_PROMPT` → `invoke_json`), TA bot RAG (FAISS + Titan embeddings + Bedrock), student memory (`llm/memory.py`), Streamlit UI with i18n (JA/EN), SQLite + seed data, dashboard charts.
- **Teacher**: FastAPI service with auth, materials, question seeds (+ local candidates), generation-context preview with readiness checks, analytics dashboard with teacher action list, evidence view, expanded lecture plan, per-student insights; Streamlit UI; seeded courses/lectures/materials/metrics; smoke-test checklist; teacher→student sync contract draft.
- **Shared**: development plan, and now data model + API spec documents.

## 3. Gaps (ranked)

1. Deploy managed PostgreSQL, S3, Cognito/university SSO, KMS, backups, and alarms.
2. Approve university retention and student-data governance policies.
3. Calibrate live Bedrock quality gates with instructor-reviewed course examples.
4. Replace the local service token with least-privilege production IAM/OAuth.

## 4. Revised roadmap — `eval/` as a parallel, cross-cutting subsystem

The original plan places LLM evaluation in Phase 6 (the end). We **promote it to a cross-cutting subsystem that runs alongside Phases 2–3**, for two reasons:

- The student side is *already* making real LLM calls, so quality can (and should) be measured now, not after integration.
- The evaluation system's synthetic-data generator **doubles as the supply that turns teacher-side seed data into realistic submissions** — one build, two payoffs.

`eval/` minimum viable scope (detailed in `evaluation-system-design.md`):

1. **Synthetic student/teacher data generation** — LLM-driven personas that answer assignments, producing realistic submissions.
2. **LLM-as-judge quality scoring** — scores grading, generation, and analytics quality (consistency, hallucination, citation grounding).
3. **Threshold gates** — scores below a bar fail; becomes the shared quality constraint binding both independently-developed groups.

### Timeline

| Track | Now → next | Then | Integration |
|---|---|---|---|
| **Student (2 devs)** | Harden grading/generation prompts; expose them to `eval/`. | Adopt shared concept taxonomy + difficulty enum; feed submissions to analytics. | Move to shared API/DB; role-based auth. |
| **Teacher (2 devs)** | Implement `teacher/services/` LLM analytics (replace rule-based evidence/plan). Consume synthetic submissions from `eval/`. | Wire live submissions → analytics. | Materials → shared RAG; seeds → shared generation via `POST /backend/assignments/generate`. |
| **Shared / eval (all 4, rotating)** | Stand up `eval/` MVP (personas + LLM-judge + one gate). Keep `data-model.md` / `api-spec.md` current. | Add gates per subsystem; author `aws-collaboration.md` + architecture diagram. | Unify DB/auth/RAG per `data-model.md` §4. |

### Immediate next actions

- [x] Eval: scaffold `eval/` with the shared `bedrock_client`, 3–4 student personas, and a grading-consistency judge with one threshold gate. *(done: `eval/`, mock + live providers.)*
- [x] Eval → Teacher: route synthetic submissions into teacher analytics inputs. *(done: `eval.run --target teacher-feed` + `teacher/db/seed_from_eval.py`; derives `ConceptMetric.wrong_rate` and synthetic `StudentProfile` rows.)*
- [x] Teacher: LLM narration for `analytics.py` (evidence, teacher actions, lecture-plan) via `teacher/services/analytics_llm.py` behind `TEACHER_USE_LLM`, with rule-based fallback. *(done)*
- [x] Eval: generation + TA-bot judges and gates, plus CI in `.github/workflows/eval-gates.yml`. *(done: step 3)*
- [x] Eval: analytics-faithfulness judge/gate over the teacher numeric facts. *(done: step 4)*
- [ ] Shared: agree the concept taxonomy (C5, now aligned in the eval feed) and a single difficulty enum (C7) so student and teacher vocabularies unify.
- [ ] Docs: author `aws-collaboration.md` and an architecture diagram (Phase 1 leftovers).

## 5. Definition of "integration-ready"

- One `users` table with role-based auth (`data-model.md` §4).
- Teacher analytics computed from real `submissions`, not seeds.
- Teacher analytics/plan produced by LLM, not rule-based strings.
- Shared assignment generation (`POST /backend/assignments/generate`) honoring teacher `required` seeds.
- All LLM subsystems (grading, generation, analytics, TA bot) pass their `eval/` threshold gates.
- Shared RAG fed by teacher `materials`.
