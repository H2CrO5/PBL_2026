# Reference Material: Data Structures and Complexity

Material ID: TG02-REF-DATA-STRUCTURES
Lecture Group: TG02 Data Structures and Complexity
Material Type: book-reference-style
Estimated Reading Time: 30 minutes
Teacher Workflows Supported: material review, question seed authoring, generation context review, class analytics, weak-point analysis, lecture improvement suggestions

## 1. Overview

Data structures are ways to organize data so that useful operations become easier. Students should not choose a structure because it is familiar. They should choose based on what the program needs to do most often.

This reference uses teacher dashboard examples so that the Teacher Part can test material ingestion, question seed authoring, generation context review, class analytics, weak-point analysis, and lecture improvement suggestions.

## 2. Operation-First Design

The central design question is:

"What operation will happen most often?"

Examples:

- If the program must preserve quiz score order, a list is appropriate.
- If the program must look up a student by ID, a dictionary is appropriate.
- If the program must check whether a student submitted work, a set is appropriate.
- If the program must undo the latest action, a stack is appropriate.
- If the program must process requests in arrival order, a queue is appropriate.

Teacher analytics should reward explanations that connect the data structure to the operation.

## 3. Lists

A list stores items in sequence. Lists are useful when order matters or when every item must be processed.

Example:

```text
scores = [88, 92, 76, 92]
```

Useful list operations:

- append a score
- get the first score
- get the last score
- traverse all scores
- compute a sum or average

Typical complexity:

| Operation | Complexity | Reason |
| --- | --- | --- |
| access by index | O(1) | direct position access |
| traverse all items | O(n) | visits each item |
| membership by scan | O(n) | may inspect many items |

Common misconception:

- Students may assume a list is always best because it is easy to write. This is weak operation-first reasoning.

## 4. Dictionaries or Maps

A dictionary stores key-value pairs. Each key maps to a value.

Example:

```text
student_report = {
    "S001": "needs edge-case practice",
    "S002": "ready for challenge task",
    "S003": "needs tracing support"
}
```

Use a dictionary when:

- each record has a unique identifier
- lookup by identifier is common
- values are updated by identifier

Typical complexity:

| Operation | Complexity | Reason |
| --- | --- | --- |
| lookup by key | about O(1) average | key directs the lookup |
| update by key | about O(1) average | key identifies the value |
| traverse all key-value pairs | O(n) | every pair is visited |

Weak-point signal:

- If a student cannot identify the key, they may not understand dictionary design.

## 5. Sets

A set stores unique values. Sets are strong for membership checks and duplicate removal.

Example:

```text
submitted_ids = {"S001", "S004", "S009"}
```

Use a set when:

- each value should appear once
- the main question is "is this value present?"
- order is not required

Typical complexity:

| Operation | Complexity | Reason |
| --- | --- | --- |
| add item | about O(1) average | direct membership structure |
| membership check | about O(1) average | avoids full scan in common cases |
| traverse all items | O(n) | every item is visited |

Common misconception:

- Students may expect a set to keep duplicates. A set removes duplicates by definition.

## 6. Stacks

A stack follows last in, first out behavior.

Example use in a teacher tool:

- A teacher edits material title, tags, and description.
- Undo should reverse the most recent edit first.
- A stack is a good fit because the latest action is undone first.

Operations:

| Operation | Meaning | Complexity |
| --- | --- | --- |
| push | add item to top | O(1) |
| pop | remove top item | O(1) |
| peek | view top item | O(1) |

Weak-point signal:

- If a student uses a stack to process help requests fairly, they may have reversed stack and queue behavior.

## 7. Queues

A queue follows first in, first out behavior.

Example use in a teacher tool:

- Assignment submissions arrive over time.
- A grading worker processes the oldest ungraded submission first.
- A queue is a good fit because arrival order should be preserved.

Operations:

| Operation | Meaning | Complexity |
| --- | --- | --- |
| enqueue | add item to back | O(1) |
| dequeue | remove item from front | O(1) with proper implementation |
| peek | view front item | O(1) |

Weak-point signal:

- If a student handles the newest help request first without a stated reason, classify as queue behavior confusion.

## 8. Worked Example: Missing Homework

Problem:

Given enrolled student IDs and submitted student IDs, return IDs for students who did not submit homework.

Input:

```text
enrolled_ids = ["S001", "S002", "S003", "S004"]
submitted_ids = ["S001", "S004"]
```

Recommended structures:

- keep enrolled_ids as a list because every enrolled student must be checked
- convert submitted_ids to a set because membership checks are frequent
- store missing IDs in a list because the output may need order

Pseudocode:

```text
submitted_set = set made from submitted_ids
missing = empty list
for each id in enrolled_ids:
    if id is not in submitted_set:
        add id to missing
return missing
```

Trace:

| id | in submitted_set? | action |
| --- | --- | --- |
| S001 | yes | do not add |
| S002 | no | add S002 |
| S003 | no | add S003 |
| S004 | yes | do not add |

Expected output:

```text
["S002", "S003"]
```

Complexity explanation:

- Building the set is O(m), where m is the number of submitted IDs.
- Traversing enrolled IDs is O(n), where n is the number of enrolled IDs.
- Each membership check is about O(1) average.
- Overall expected work is O(n + m).

## 9. Question Seed Bank

### Seed 1: Choose a Structure

Prompt:

A teacher needs to store quiz scores in the order they were submitted. Scores may repeat. Choose a data structure and justify the choice.

Expected answer:

- Use a list.
- Order matters.
- Duplicate scores are allowed.

Rubric:

| Criterion | Points |
| --- | ---: |
| chooses list | 3 |
| mentions order | 3 |
| mentions duplicates or traversal | 2 |
| explanation is clear | 2 |

### Seed 2: Missing Homework

Prompt:

Given enrolled student IDs and submitted student IDs, return the IDs that have not submitted. Use a structure that makes membership checks efficient.

Expected answer:

- Use a set for submitted IDs.
- Traverse enrolled IDs.
- Add IDs not present in submitted set to a missing list.

Rubric:

| Criterion | Points |
| --- | ---: |
| uses or proposes set for submitted IDs | 3 |
| checks every enrolled ID | 2 |
| returns only missing IDs | 2 |
| handles all-submitted case | 1 |
| explains O(n + m) or similar traversal cost | 2 |

### Seed 3: Teacher Dashboard Design

Prompt:

Design data structures for these Teacher Part features:

1. Look up a student report by student ID.
2. Process assignment generation jobs in request order.
3. Undo the most recent material metadata edit.
4. Track unique concept tags attached to uploaded materials.

Expected answer:

- dictionary for student report lookup by ID
- queue for jobs in request order
- stack for undo
- set for unique concept tags

Rubric:

| Criterion | Points |
| --- | ---: |
| dictionary choice and key explanation | 3 |
| queue choice and first-in explanation | 2 |
| stack choice and last-in explanation | 2 |
| set choice and uniqueness explanation | 2 |
| clear operation-first reasoning | 1 |

## 10. Class Analytics Design Notes

Recommended concept dimensions:

- list_usage
- dictionary_lookup
- set_membership
- stack_queue_behavior
- complexity_reasoning
- data_modeling

Example aggregate report:

| Concept | Correct Rate | Main Error Pattern | Recommended Action |
| --- | ---: | --- | --- |
| list_usage | 86 percent | minor explanation gaps | continue to applied tasks |
| set_membership | 54 percent | uses list scan for membership | compare list scan vs set lookup |
| dictionary_lookup | 63 percent | key and value reversed | mark key/value in examples |
| stack_queue_behavior | 58 percent | stack and queue reversed | use request-line simulation |
| complexity_reasoning | 49 percent | labels memorized without reason | require operation-first explanation |

Analytics interpretation:

- High correctness with weak explanations suggests students can imitate examples but need justification practice.
- Low correctness on set membership may indicate students do not yet connect structure choice to runtime.
- Repeated stack/queue reversal is usually a conceptual model issue, not a syntax issue.

## 11. Individual Student Analysis Notes

Student C:

- strength: chooses lists correctly for ordered data
- weak point: overuses lists for lookup tasks
- evidence: student used a list of pairs to find reports by ID without explaining scan cost
- suggested feedback: "When you have a stable ID and frequent lookup, consider a dictionary."
- next practice: two key-value mapping exercises

Student D:

- strength: explains set uniqueness
- weak point: stack and queue behavior reversal
- evidence: student says a queue removes the newest request first
- suggested feedback: "A queue preserves arrival order. The first request added is the first handled."
- next practice: classify five real-world workflows as stack or queue

Student E:

- strength: solves missing homework output correctly
- weak point: weak complexity explanation
- evidence: answer says "fast" but does not explain visited items or membership checks
- suggested feedback: "Name the repeated operation and explain how many times it happens."
- next practice: write one complexity sentence for each solved task

## 12. Weak-Point Labels

Use these labels in reports:

- list_overuse
- missing_key_value_model
- set_duplicate_confusion
- stack_queue_reversal
- membership_complexity_gap
- operation_first_reasoning_gap

Example weak-point rule:

If a student chooses a list for frequent membership checks and does not mention scan cost, assign:

- list_overuse
- membership_complexity_gap

## 13. Lecture Improvement Suggestions

Use these rules for teacher-facing recommendations:

| Analytics Trigger | Improvement Suggestion |
| --- | --- |
| list_overuse appears in more than 35 percent of answers | add a list-vs-set membership demonstration |
| dictionary key errors appear in more than 25 percent of answers | add a key/value marking warm-up |
| stack_queue_reversal appears in more than 20 percent of answers | use a physical request-line activity |
| complexity explanations average below 60 percent | require every solution to identify the repeated operation |
| students choose correct structures but cannot justify | add short written "why this structure" prompts |

## 14. Suggested Next Lecture

Recommended next lecture if the class is ready:

- Searching and Sorting Patterns

Recommended remedial lecture if weak points remain:

- Membership, Lookup, and Operation-First Structure Choice

Reason:

- Searching and sorting require students to understand why data organization affects work. If structure choice is weak, searching and sorting will feel like isolated recipes.
