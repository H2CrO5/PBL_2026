# eval/ — LLM subsystem evaluation harness (MVP)

Cross-cutting quality harness for the LLM-based education system. It runs in
parallel with module development (not only at the end) and turns LLM output
quality into a **pass/fail constraint** shared by both the Student and Teacher
groups. Design: `docs/evaluation-system-design.md`.

## What the MVP does

1. **Synthetic students** — 3–4 personas (`personas/`) answer assignments.
2. **Grading consistency judge** — grades the *same* answer N times through the
   student backend's real grading prompt (`judges/grading.py`) and measures how
   stable the score/verdict are.
3. **Threshold gate** — `gates/thresholds.py` fails the run (exit code 1) if a
   metric is below its bar.

Synthetic answers/submissions produced here are also the intended supply to
replace the teacher side's mock data (later step).

## Run

Offline mock (default — no AWS required):

```bash
python -m eval.run --target grading
```

Options:

```bash
python -m eval.run --target grading --repeats 5     # more grading repeats
python -m eval.run --target grading --jitter 0.4    # simulate an inconsistent grader (mock)
python -m eval.run --target grading --live          # real Bedrock (needs AWS creds)
```

Teacher-analytics feed (step 2) — aggregate synthetic grading into a feed the
teacher module imports instead of hand-seeded numbers:

```bash
python -m eval.run --target teacher-feed            # writes eval/reports/teacher_feed.json
cd teacher && python -m db.seed && python -m db.seed_from_eval
```

Generation and TA-bot gates (step 3) — judge the student's real generation and
TA prompts at the prompt level (no student endpoint required):

```bash
python -m eval.run --target generation              # question validity / concept / difficulty
python -m eval.run --target ta-bot                  # citation grounding / hallucination
python -m eval.run --target generation --jitter 0.5 # mock: demonstrate a failing gate
```

Analytics-faithfulness gate (step 4) — independently narrate the teacher's
numeric facts and judge whether the narration stays faithful to them (decoupled
from the teacher module code):

```bash
python -m eval.run --target analytics                                   # uses datasets/analytics_facts.json
python -m eval.run --target analytics --live --cases eval/reports/teacher_feed.json  # judge the real synthetic feed
```

Full black-box workflow — requires all four local services to be running. It
creates a lecture, uploads and indexes a Markdown material, verifies publish/hide/republish
visibility from the Student API, generates a Teacher draft through Bedrock,
publishes and submits an assignment, invokes the configured grader, and checks
the resulting progress delta and timeline:

```bash
python -m eval.run --target workflow
```

Concurrent Student smoke/load test — each flow logs in, reads auth, dashboard,
timeline, materials and assignments, then logs out. The test also verifies that
logging out one of two sessions for the same student does not invalidate the
other session:

```bash
python eval/stress.py --requests 60 --concurrency 15
python eval/stress.py --requests 300 --concurrency 50
```

Teacher-side sessions, analytics, materials and generation-context reads can be
tested separately. The optional generation phase invokes real Bedrock and
creates drafts in the target Teacher database, so use an isolated database:

```bash
python eval/stress_teacher.py --flows 60 --concurrency 15
python eval/stress_teacher.py --flows 150 --concurrency 30 \
  --generation-requests 6 --generation-concurrency 3
```

This is a local correctness and regression load test, not a production capacity
benchmark. SQLite and password hashing intentionally limit throughput; use the
PostgreSQL deployment configuration for production sizing.

Run from the repository root so `python -m eval.run` resolves the package.

## Modes

- **mock** (default): deterministic, offline, no AWS. `--jitter` injects grader
  variance to demonstrate a failing gate. Good for scaffolding and CI wiring.
- **live** (`--live`): reuses `student/llm/bedrock_client.py` and the real
  Bedrock model. Requires AWS credentials / `AWS_BEARER_TOKEN_BEDROCK`.

## Metrics (MVP)

| Target | Metric | Meaning | Gate |
|---|---|---|---|
| grading | `grading_consistency` | 1 − (score spread / 100), averaged over cases×personas | `>= 0.90` |
| grading | `correctness_agreement` | fraction of cases×personas where all repeats agree on is_correct | `>= 0.90` |
| generation | `question_validity` | judge: generated question is well-formed with a correct answer | `>= 0.90` |
| generation | `concept_match` | judge: question targets the requested concept | `>= 0.85` |
| generation | `difficulty_match` | judge: question matches the requested difficulty | `>= 0.80` |
| ta-bot | `citation_grounding_rate` | judge: fraction of answer claims supported by the sources | `>= 0.85` |
| ta-bot | `hallucination_rate` | judge: fraction of answer claims unsupported/contradicted | `<= 0.05` |
| analytics | `analytics_faithfulness` | judge: narration's claims follow from the numeric facts (no invented figures) | `>= 0.80` |
| workflow | `workflow_success` | all Teacher-to-Student material, assignment and progress checks pass | `>= 1.00` |

Thresholds are starting values in `gates/thresholds.py`; calibrate from a
baseline run, then ratchet up.

## Output

A JSON report is written to `eval/reports/<target>_<timestamp>.json` (git-ignored).
The process exit code is `0` on pass, `1` on fail.

## Layout

```
eval/
  run.py                entrypoint (python -m eval.run)
  llm.py                MockProvider / BedrockProvider
  reuse.py              imports student prompts / Bedrock client (no duplication)
  personas/             persona definitions + answer simulation
  judges/grading.py     grading consistency judge
  judges/generation.py  assignment-generation judge
  judges/ta_bot.py      TA-bot grounding / hallucination judge
  judges/analytics.py   analytics-faithfulness judge
  gates/thresholds.py   metric thresholds + pass/fail
  datasets/*.json       fixtures: assignments / generation / TA / analytics facts
  workflows/            live-service Teacher-to-Student black-box workflow
  stress.py             concurrent Student session/read smoke and load test
  stress_teacher.py     concurrent Teacher reads and optional Bedrock generation
  reports/              run reports (git-ignored)
```

## CI

`.github/workflows/eval-gates.yml` runs the grading, generation, TA-bot, and
analytics gates in mock mode on pull requests that touch `student/llm/**`,
`student/api/routers/assignments.py`, `student/api/routers/chat.py`,
`teacher/services/**`, or `eval/**`. Mock mode is standard-library only, so it
needs no AWS credentials and makes no paid calls; a failing gate blocks merge.

## Not in the MVP (next steps)

DB-backed `eval_runs`/`eval_cases` tables and threshold ratcheting from a larger
baseline. Steps 1–4 (grading, teacher-feed, generation, TA-bot, and
analytics-faithfulness judges + CI) are done. See
`docs/evaluation-system-design.md` section 6.
