# Evaluation System Design (`eval/`)

Status: implemented MVP. Offline/CI gates cover grading consistency, generation,
TA grounding/hallucination, and analytics faithfulness; live Bedrock mode is
available for calibrated runs.

Related: `status-and-roadmap.md` (§4 promotes this to a parallel subsystem), `data-model.md` (§5 eval tables), `api-spec.md` (LLM endpoints under test).

---

## 1. Motivation

- The student side makes real Bedrock calls that require measurable consistency
  and grounding constraints.
- Teacher analytics consumes real submissions when integration is enabled and
  synthetic feeds remain useful for repeatable development.
- Shared threshold gates bind both independently developed applications.

One subsystem addresses all three: an LLM-driven evaluation harness that (a) generates realistic synthetic data, (b) judges subsystem output quality, and (c) enforces threshold gates as a shared constraint.

## 2. Design principles

- **Cross-cutting, not end-phase.** Runs in parallel with Phases 2–3, not saved for Phase 6.
- **Reuse, don't fork.** Use the existing `student/llm/bedrock_client.py` (`invoke`, `invoke_json`) for all LLM calls, including judges and personas. Same model config (`api-spec.md` §4).
- **Dual payoff.** The synthetic-data generator is also the supply that replaces teacher-side seed data with realistic submissions.
- **Deterministic where possible.** Fixed persona seeds and judge prompts, low temperature for judges, so scores are comparable across runs / git SHAs.
- **A gate is a constraint.** Each subsystem has a threshold; below it, the run fails. This is the mechanism that makes evaluation "a constraint for the whole system."

## 3. Three MVP components

### 3.1 Synthetic student/teacher data generation

LLM acts as the **"student"**: personas with an ability level and a misconception profile answer real assignments produced by the student backend.

- Personas: e.g. `strong`, `average`, `struggling`, `misconception-prone`. Stored in `eval_personas` (`data-model.md` §5).
- A persona is given an assignment (`question_text`, `choices`, `question_type`) and a system prompt that constrains it to behave at its ability level, then answers via `bedrock_client.invoke`.
- Answers are submitted through the normal grading path, producing **realistic `submissions`** (flagged `source = "synthetic"`).
- These submissions feed **teacher analytics** (dashboard, evidence view, lecture plan), so the teacher side can be developed and demoed before any real student traffic exists.

LLM can also act as the **"teacher"**: generate plausible teacher question seeds / rubrics to stress-test the generation-context preview and seed handling.

### 3.2 LLM-as-judge quality scoring

A separate LLM (low temperature) scores subsystem outputs against explicit rubrics. Targets and metrics:

| Target subsystem | What is judged | Example metrics |
|---|---|---|
| **Grading** (`POST /assignments/submit`) | Is the score/verdict correct and consistent for the same answer? Does feedback match the rubric? | `grading_consistency`, `rubric_alignment`, `score_variance` |
| **Assignment generation** | Is the generated question valid, on-concept, at the requested difficulty, with a correct answer? | `question_validity`, `concept_match`, `difficulty_match` |
| **TA bot** (`POST /chat/message`) | Is the answer grounded in retrieved sources? Any hallucination? | `citation_grounding_rate`, `hallucination_rate`, `answer_relevance` |
| **Teacher analytics** (once LLM-driven) | Do weak concepts / evidence / recommendations follow from the submission data? | `analytics_faithfulness`, `recommendation_actionability` |

Judge outputs a numeric score + rationale per case (`eval_cases`), aggregated into `eval_scores` per run.

Consistency check: submit the **same answer multiple times** and measure score variance — cheap, high-signal for an LLM grader.

### 3.3 Threshold gates (the constraint)

Each metric has a threshold. A run fails if any gate fails.

```
grading_consistency        >= 0.90
rubric_alignment           >= 0.80
citation_grounding_rate    >= 0.85
hallucination_rate         <= 0.05
question_validity          >= 0.90
```

(Starting values — calibrate against a first baseline run, then ratchet up.)

Gates run in two modes:

- **Local**: `python -m eval.run --target grading` before pushing.
- **CI**: on PRs touching `student/llm/**`, `student/api/routers/assignments.py`, `student/api/routers/chat.py`, or `teacher/services/**`, run the relevant gate and block merge on failure. This is the shared constraint both groups are bound by.

## 4. Proposed layout

```
eval/
├── README.md
├── run.py                 # entrypoint: --target grading|generation|ta_bot|analytics
├── personas/
│   ├── definitions.py     # persona specs (ability, misconceptions)
│   └── simulate.py        # persona answers an assignment via bedrock_client
├── judges/
│   ├── grading_judge.py
│   ├── generation_judge.py
│   ├── ta_bot_judge.py
│   └── prompts.py         # judge system prompts + rubrics
├── gates/
│   └── thresholds.py      # metric -> threshold, pass/fail logic
├── datasets/
│   └── seed_cases.json    # fixed evaluation cases for reproducibility
└── store.py               # writes eval_runs / eval_cases / eval_scores
```

Reuse: import `bedrock_client` and `prompts` from the student module (or a shared package once the backend is unified). Do **not** duplicate the Bedrock client.

## 5. Metrics reference

| Metric | Definition | Direction |
|---|---|---|
| `grading_consistency` | 1 − normalized score variance over N repeats of the same answer | higher better |
| `rubric_alignment` | judge score: does feedback reflect the rubric | higher better |
| `question_validity` | judge score: question is well-formed with a correct answer | higher better |
| `concept_match` | generated item targets the requested concept | higher better |
| `difficulty_match` | generated item matches requested difficulty | higher better |
| `citation_grounding_rate` | fraction of TA-bot claims supported by retrieved sources | higher better |
| `hallucination_rate` | fraction of TA-bot claims unsupported/contradicted | lower better |
| `analytics_faithfulness` | reported weak concepts / evidence follow from submission data | higher better |

## 6. Rollout

- **Step 1 (MVP) — done:** personas (3–4) + grading judge + one `grading_consistency` gate (`eval/`, `python -m eval.run --target grading`). Mock provider runs offline; live provider reuses the student Bedrock client.
- **Step 2 — done:** synthetic grading is aggregated into a teacher-analytics feed (`python -m eval.run --target teacher-feed`) and imported into the teacher DB (`teacher/db/seed_from_eval.py`), deriving `ConceptMetric.wrong_rate` and synthetic `StudentProfile` rows instead of hand-seeded numbers. Eval cases are tagged with the teacher's concept vocabulary (addresses C5).
- **Step 3 — done:** generation and TA-bot judges + gates (`python -m eval.run --target generation | ta-bot`), judged at the prompt level so no student endpoint is required; CI wired in `.github/workflows/eval-gates.yml` (mock mode, no AWS) on the relevant paths.
- **Step 4 — done:** analytics-faithfulness judge (`python -m eval.run --target analytics`). Decoupled from the teacher module: it takes the numeric facts (teacher_feed.json schema), independently narrates them, and judges whether the narration stays faithful (no invented figures / contradictions). Threshold calibrated to `>= 0.80` from live baseline runs.
- **Step 5:** calibrate thresholds from a larger baseline; ratchet upward; use in Phase 6 as the LLM evaluation report.

## 7. Open questions

- Judge model: same Haiku model, or a stronger model for judging (self-evaluation bias)? Recommend a stronger judge model where budget allows.
- Cost budget per run (number of personas × cases × repeats).
- Where synthetic submissions live before the shared DB exists (student DB vs a dedicated eval DB).
- Human spot-check cadence to validate that the LLM judge itself is trustworthy.
