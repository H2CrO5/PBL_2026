# Status and Roadmap

Companion to `development-plan.md`. The plan describes the intended process; this document records **where the project actually is** and what to do next. Reflects the `setup/initial-environment` branch as of commit `337bc65`.

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
| **Teacher** | Phase 4 (in progress) | **Rich workflow UI + analytics — but still no LLM.** Now includes evidence view, teacher action list, seed candidates, backend readiness checks, and expanded lecture plans. All of it is **rule-based Python over deterministic seed data** (confirmed: no Bedrock anywhere in `teacher/`). Scope is deliberately **post-slide**: structure completed materials, do not generate slides. |
| **Shared backend** | Phase 2 (partial) | Not started as shared infrastructure. Two independent SQLite DBs and two FastAPI services. Assignment-generation contract exists only as a draft (`STUDENT_SYNC_README.md`). |
| **Docs** | Phase 1 | Plan + sync README exist; `data-model.md` / `api-spec.md` now added. Architecture diagram and AWS collaboration doc still missing. |
| **Evaluation** | Phase 6 in plan | **Not started.** Re-scoped here to run in parallel with Phases 2–3 (see §4). |

Summary: the **student side is genuinely functional** with live LLM; the **teacher side is an increasingly sophisticated facade over seed data with no LLM**; and there is **no quality measurement** anywhere despite the student side already making real LLM calls.

---

## 2. What is done

- **Student**: real Bedrock client with dual auth (Bearer / SigV4), LLM grading (`GRADING_PROMPT` → `invoke_json`), TA bot RAG (FAISS + Titan embeddings + Bedrock), student memory (`llm/memory.py`), Streamlit UI with i18n (JA/EN), SQLite + seed data, dashboard charts.
- **Teacher**: FastAPI service with auth, materials, question seeds (+ local candidates), generation-context preview with readiness checks, analytics dashboard with teacher action list, evidence view, expanded lecture plan, per-student insights; Streamlit UI; seeded courses/lectures/materials/metrics; smoke-test checklist; teacher→student sync contract draft.
- **Shared**: development plan, and now data model + API spec documents.

## 3. Gaps (ranked)

1. **Teacher-side AI is unimplemented.** The teacher's core value — class understanding, misconception trends, evidence, lecture recommendations — is computed by hand-written rules over seed data. The workflow shape is well-developed, but no reasoning is LLM-driven. Target: implement in `teacher/services/` reusing the student `bedrock_client` pattern.
2. **No evaluation / quality measurement.** The student side calls the LLM but nothing measures grading consistency, hallucination, or citation grounding. Without this, quality problems surface only after integration.
3. **The core data flow is not wired.** "Student submissions → teacher analytics" is entirely mocked. Teacher analytics has no live source.
4. **Schema divergence.** Student and teacher databases model "student" twice (`students` vs `student_profiles`), disagree on lecture scope, and use different difficulty vocabularies. See `data-model.md` conflicts C1–C7.
5. **Missing infrastructure docs.** No architecture diagram, no `aws-collaboration.md` (referenced by the plan), no shared auth/DB decision.

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

- [ ] Teacher: replace rule-based `analytics.py` (evidence, teacher actions, lecture-plan) with `teacher/services/*` LLM calls.
- [ ] Eval: scaffold `eval/` with the shared `bedrock_client`, 3–4 student personas, and a grading-consistency judge with one threshold gate.
- [ ] Eval → Teacher: route synthetic submissions into teacher analytics inputs.
- [ ] Shared: agree the concept taxonomy (C5) and a single difficulty enum (C7) so student and teacher vocabularies unify.
- [ ] Docs: author `aws-collaboration.md` and an architecture diagram (Phase 1 leftovers).

## 5. Definition of "integration-ready"

- One `users` table with role-based auth (`data-model.md` §4).
- Teacher analytics computed from real `submissions`, not seeds.
- Teacher analytics/plan produced by LLM, not rule-based strings.
- Shared assignment generation (`POST /backend/assignments/generate`) honoring teacher `required` seeds.
- All LLM subsystems (grading, generation, analytics, TA bot) pass their `eval/` threshold gates.
- Shared RAG fed by teacher `materials`.
