# Slide Material: Data Structures for Storing and Searching Course Data

Material ID: TG02-SLIDES-DATA-STRUCTURES
Lecture Group: TG02 Data Structures and Complexity
Material Type: slide-style
Estimated Duration: 80 minutes
Teacher Workflows Supported: material review, question seed authoring, generation context review, class analytics, weak-point analysis, lecture improvement suggestions

## Material Tags

- lists
- dictionaries
- sets
- stacks
- queues
- lookup
- traversal
- complexity
- data modeling

## Slide 1: Teaching Goal

Students should learn how to choose a data structure based on the operation they need most often.

By the end of the lecture, students should be able to:

- explain when a list is appropriate
- explain when a dictionary or map is appropriate
- use a set for membership and uniqueness
- distinguish stack behavior from queue behavior
- connect common operations to expected complexity
- justify a data structure choice in one or two sentences

## Slide 2: Course Data Scenario

Scenario:

A teacher wants to review course activity:

- a list of submitted quiz scores
- a table of student ID to student name
- a set of students who submitted homework
- a queue of help requests
- a stack of recently opened material pages

Teacher prompt:

- Ask which structure best fits each data need.
- Ask what operation the teacher is likely to do most often.

## Slide 3: Lists

A list stores items in order.

Use a list when:

- order matters
- duplicates are allowed
- you need to visit every item
- you need positions such as first, second, or last

Example:

```text
scores = [75, 90, 68, 90]
```

Good operations:

- append a new score
- traverse all scores
- compute average

Weak choice:

- using a list for frequent membership checks on a very large collection

## Slide 4: Dictionaries or Maps

A dictionary stores key-value pairs.

Use a dictionary when:

- each item has a unique key
- fast lookup by key matters
- values need to be updated by identifier

Example:

```text
student_names = {
    "S001": "Aki",
    "S002": "Mina",
    "S003": "Ren"
}
```

Teacher workflow example:

- Look up one student's analytics report by student ID.

## Slide 5: Sets

A set stores unique values.

Use a set when:

- duplicates should be removed
- membership checks are frequent
- order is not the main concern

Example:

```text
submitted_ids = {"S001", "S003", "S010"}
```

Teacher workflow example:

- Check whether each enrolled student submitted the assignment.

## Slide 6: Stack

A stack uses last in, first out behavior.

Useful mental model:

- The most recently added item is removed first.

Example use:

- undo actions
- browser back history
- recently opened material pages

Operations:

- push: add to top
- pop: remove from top
- peek: view top

## Slide 7: Queue

A queue uses first in, first out behavior.

Useful mental model:

- The earliest added item is handled first.

Example use:

- help desk questions
- grading jobs
- upload processing
- classroom check-in line

Operations:

- enqueue: add to back
- dequeue: remove from front
- peek: view front

## Slide 8: Operation-First Thinking

Ask this before choosing a structure:

"What will I do most often?"

| Need | Likely Structure |
| --- | --- |
| keep ordered scores | list |
| look up student by ID | dictionary |
| check if submitted | set |
| undo the last action | stack |
| process requests in arrival order | queue |

Teacher prompt:

- Give students a data need and ask for the most important operation.

## Slide 9: Complexity Snapshot

Typical introductory complexity expectations:

| Structure | Operation | Expected Complexity |
| --- | --- | --- |
| list | visit all items | O(n) |
| list | check membership by scanning | O(n) |
| dictionary | lookup by key | about O(1) average |
| set | membership check | about O(1) average |
| stack | push or pop top | O(1) |
| queue | enqueue or dequeue | O(1) with proper implementation |

Teacher note:

- Avoid overloading students with implementation details. Focus on operation choice.

## Slide 10: Mini Activity

Task:

"Find students who enrolled but did not submit homework."

Candidate structures:

- enrolled_ids as a list
- submitted_ids as a set
- missing_ids as a list

Pseudocode:

```text
missing = empty list
for each id in enrolled_ids:
    if id is not in submitted_ids:
        add id to missing
return missing
```

Expected reasoning:

- traverse enrolled IDs once
- use set membership to avoid repeatedly scanning the submitted list

## Slide 11: Question Seed Candidates

Seed A: Basic

- Prompt: Choose the best data structure for storing ordered quiz scores and explain why.
- Concepts: list, order, traversal
- Difficulty: easy
- Expected answer: list because scores may be processed in order and duplicates are allowed

Seed B: Intermediate

- Prompt: Given enrolled IDs and submitted IDs, return IDs that have not submitted. Use an efficient structure for membership checks.
- Concepts: set, membership, list traversal, complexity
- Difficulty: medium
- Expected answer: use a set for submitted IDs and traverse enrolled IDs

Seed C: Challenge

- Prompt: Design structures for a teacher dashboard that supports student lookup by ID, assignment processing in arrival order, and undoing the most recent material edit.
- Concepts: dictionary, queue, stack, operation-first design
- Difficulty: hard
- Expected answer: dictionary for lookup, queue for processing, stack for undo

## Slide 12: Class Analytics Hooks

Track these signals after students submit work:

- percent of students who justify structure choice by operation
- percent of students who confuse lists and sets
- percent of students who use dictionaries only when keys are unique
- percent of students who distinguish stack from queue
- percent of students who connect membership checks to complexity

Suggested dashboard metrics:

| Metric | Healthy Signal | Warning Signal |
| --- | --- | --- |
| list vs set choice | mentions order or uniqueness | chooses by habit only |
| dictionary use | identifies key and value | uses list of pairs for lookup |
| stack vs queue | explains last-in or first-in | reverses behavior |
| complexity reasoning | links operation to growth | memorizes labels only |

## Slide 13: Weak-Point Map

| Weak Point | Observable Evidence | Suggested Intervention |
| --- | --- | --- |
| list overuse | uses list for every task | ask for main operation before coding |
| set misunderstanding | expects set to preserve duplicates | use duplicate-removal example |
| dictionary key confusion | stores non-unique keys | identify stable ID before mapping |
| stack/queue reversal | handles newest request first in a help line | compare undo vs service line |
| complexity memorization | states O(1) without operation context | require one-sentence justification |

## Slide 14: Lecture Improvement Suggestions

If analytics show list overuse:

- add a comparison activity where the same task is solved with list scanning and set membership

If analytics show stack/queue reversal:

- add a classroom simulation with request cards

If analytics show weak dictionary reasoning:

- add exercises where students mark the key and value in a real dataset

If analytics show complexity memorization:

- require each answer to complete the sentence: "This is efficient because..."

## Slide 15: Next Lecture Bridge

Bridge options:

- If students understand structure choice, move to searching and sorting.
- If students struggle with membership and lookup, review lists, sets, and dictionaries with more examples.

Exit ticket:

- "For a teacher dashboard, name one feature that should use a dictionary and one feature that should use a queue."
