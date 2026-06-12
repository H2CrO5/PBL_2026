# Teacher Part Smoke Test Checklist

Purpose: validate the planned Teacher Part workflow using the sample teacher materials in `teacher/materials/`.

Scope: teacher-side tasks only. The Teacher Part manages materials, analytics, and teacher-authored question seeds. Final adaptive assignment generation belongs to the future shared backend or Student Part integration.

## Test Data

- Lecture group 1: `TG01 Algorithmic Thinking`
- Lecture group 2: `TG02 Data Structures and Complexity`
- Material types per group: one slide-style Markdown file and one book-reference-style Markdown file
- Suggested mock teacher: `teacher_demo`
- Suggested mock class: `PBL Intro Programming`

## Checklist

| Step | Teacher Task | Validation Target | Pass Criteria |
| --- | --- | --- | --- |
| 1 | Login | teacher authentication and role routing | teacher can access teacher-only dashboard or mock teacher session |
| 2 | Material review | material management page | both lecture groups appear with title, type, tags, and source file metadata |
| 3 | Material detail review | material viewer and retrieval preview | teacher can open slide-style and reference-style files; headings and tags are visible |
| 4 | Question seed review | base/required/rubric seed management | teacher can review seeded questions with difficulty, expected answer, and rubric |
| 5 | Question seed authoring | teacher-authored required question input | teacher can add a question seed tied to the selected lecture material |
| 6 | Class analytics review | class analytics dashboard | dashboard shows concept-level results, weak-point counts, common error patterns, and suggested class actions |
| 7 | Individual student analysis | student analytics page | teacher can open a student report showing strengths, weak points, evidence, feedback, and next practice |
| 8 | Next lecture suggestion | lecture recommendation feature | system recommends next lecture or remedial lecture using analytics triggers and explains the reason |
| 9 | Lecture improvement suggestion | teacher report or recommendation panel | system suggests concrete lecture changes tied to weak-point patterns |
| 10 | Generation context review | future shared-backend handoff | teacher can review material titles, weak concepts, and question seeds that will constrain backend assignment generation |

## Smoke Test Scenarios

### Scenario A: Algorithmic Thinking Question Seeds

1. Login as a teacher.
2. Open `TG01 Algorithmic Thinking`.
3. Review the slide-style material.
4. Open Question Bank for lecture group 1.
5. Confirm the seeded or newly created question includes:
   - loop traversal
   - empty-list handling
   - threshold comparison
   - rubric criteria
6. Review mock class analytics.
7. Confirm weak points can include:
   - weak decomposition
   - missing edge cases
   - wrong comparison operator
   - complexity guessing
8. Confirm next lecture suggestion can point to data structures if readiness is high, or boundary conditions and trace tables if readiness is low.

### Scenario B: Data Structures Question Seeds

1. Login as a teacher.
2. Open `TG02 Data Structures and Complexity`.
3. Review the reference-style material.
4. Open Question Bank for lecture group 2.
5. Confirm the seeded or newly created question includes:
   - dictionary for lookup by student ID
   - queue for arrival-order processing
   - stack for undo
   - set for unique concept tags
   - operation-first justification
6. Review mock class analytics.
7. Confirm weak points can include:
   - list overuse
   - missing key-value model
   - set duplicate confusion
   - stack queue reversal
   - membership complexity gap
8. Confirm lecture improvement suggestions are tied to analytics triggers.

## Minimum Acceptance Criteria

- Teacher can distinguish slide-style material from reference-style material.
- Teacher can filter or identify materials by lecture group and concept tag.
- Question seeds are tied to selected material rather than unrelated content.
- Generation context exposes material titles, weak concepts, and question seeds for the future shared backend.
- Class analytics show concept-level performance and common error patterns.
- Individual student analysis includes evidence and next practice.
- Next lecture suggestion changes when mock analytics indicate readiness versus remediation need.
- No Student Part files are required or modified for this smoke test.
