# Local Concurrency and Stress Test Report

Date: 2026-09-04
Scope: merged local `main`, including the collaborator's Student material viewer
and material-audience protection changes.

## Purpose

The tests checked concurrent authentication, session isolation, high-traffic read
paths, Student progress/material access, Teacher analytics/material access, and
real Amazon Bedrock assignment generation. They are correctness and regression
tests for the local SQLite development stack, not production capacity claims.

## Student workload

The final run executed 300 complete flows at concurrency 50. Each flow logged in,
verified the current user, read the dashboard, assignments, progress history and
published lecture materials, and logged out.

| Result | Value |
| --- | ---: |
| Successful flows | 300 / 300 |
| Intended HTTP requests | 2,105 |
| Failed flows | 0 |
| Session isolation | Passed |
| Mean flow latency | 5,970.5 ms |
| p50 flow latency | 6,109.5 ms |
| p95 flow latency | 9,873.6 ms |
| Maximum flow latency | 9,972.9 ms |

An immediately preceding run with the same 300/50 parameters completed 298
flows and recorded two client-side `ReadError` exceptions. Every completed HTTP
response in that run was 200, session isolation passed, and the API logs showed
no 5xx response or application traceback. The immediate identical repeat passed
300/300. The transient result is retained as diagnostic evidence rather than
being hidden.

Raw results:

- `eval/reports/stress_20260904T085635Z.json` — transient 298/300 run
- `eval/reports/stress_20260904T085707Z.json` — final 300/300 run

## Teacher workload

The Teacher read phase executed 150 complete flows at concurrency 30. It covered
login/logout isolation, the analytics dashboard, lectures, materials, questions,
student insights, published assignments and assignment-generation context.

The generation phase issued six real Bedrock draft-generation requests at
concurrency 3.

| Result | Value |
| --- | ---: |
| Successful Teacher flows | 150 / 150 |
| Successful Bedrock generations | 6 / 6 |
| Total HTTP 200 responses | 1,515 |
| Failed operations | 0 |
| Session isolation | Passed |
| Read throughput | 16.44 flows/s |
| Read p95 latency | 9,092.0 ms |
| Generation p95 latency | 12,593.1 ms |

Raw result:

- `eval/reports/stress_teacher_20260904T085737Z.json`

## Related regression results

- Student unit tests: 20 passed.
- Teacher unit tests: 18 passed.
- Live end-to-end workflow: 14/14 steps passed, including publish/hide/republish,
  real Bedrock draft generation, assignment publication, Student submission,
  Bedrock grading and progress updates.
- Offline grading, generation, TA grounding and analytics gates all passed.
- Browser verification confirmed that a Student can open the new material page,
  browse materials grouped by course and lecture, expand the full text, and use
  the text-download control.

## Conclusion

The merged implementation passed the final end-to-end and concurrency regression
suite. The one non-reproducing local transport event is documented above and
should be monitored if the development server is used at comparable concurrency.
Production load claims would require a production database, deployment topology,
representative network conditions and a sustained-load test.
