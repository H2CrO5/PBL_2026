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

Run from the repository root so `python -m eval.run` resolves the package.

## Modes

- **mock** (default): deterministic, offline, no AWS. `--jitter` injects grader
  variance to demonstrate a failing gate. Good for scaffolding and CI wiring.
- **live** (`--live`): reuses `student/llm/bedrock_client.py` and the real
  Bedrock model. Requires AWS credentials / `AWS_BEARER_TOKEN_BEDROCK`.

## Metrics (MVP)

| Metric | Meaning | Gate |
|---|---|---|
| `grading_consistency` | 1 − (score spread / 100), averaged over cases×personas | `>= 0.90` |
| `correctness_agreement` | fraction of cases×personas where all repeats agree on is_correct | `>= 0.90` |

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
  gates/thresholds.py   metric thresholds + pass/fail
  datasets/seed_cases.json   fixture assignments
  reports/              run reports (git-ignored)
```

## Not in the MVP (next steps)

Generation / TA-bot / analytics-faithfulness judges, DB-backed
`eval_runs`/`eval_cases` tables, and CI wiring. (Feeding synthetic submissions
into teacher analytics is done — see the teacher-feed target above.)
See `docs/evaluation-system-design.md` section 6.
