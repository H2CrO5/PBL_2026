# Reference Material: Algorithmic Thinking and Problem Decomposition

Material ID: TG01-REF-ALG-THINKING
Lecture Group: TG01 Algorithmic Thinking
Material Type: book-reference-style
Estimated Reading Time: 25 minutes
Teacher Workflows Supported: material review, question seed authoring, generation context review, class analytics, weak-point analysis, lecture improvement suggestions

## 1. Overview

Algorithmic thinking is the practice of describing a solution as precise, ordered, testable steps. In an introductory programming course, this skill matters because many errors are not syntax errors. Many errors happen earlier, when a student misunderstands the problem, omits a boundary case, or cannot explain why a loop is needed.

The teacher-side system should treat this material as a source for:

- concept tags for material management
- question prompts and rubrics for shared-backend assignment generation
- expected evidence for analytics
- weak-point labels for student reports
- next lecture recommendations

## 2. Core Concepts

### 2.1 Input

Input is the data an algorithm receives. It can come from a user, a file, a form, a database, or another function.

Examples:

- a room capacity
- a list of quiz scores
- a student's submitted answer
- a threshold score for passing

Analytics signal:

- If a student solution uses a variable that was never defined, the student may have weak input identification.

### 2.2 Output

Output is the result an algorithm must produce. Output should be clear before implementation begins.

Examples:

- "fits", "full", or "over capacity"
- the average quiz score
- a list of names
- a boolean value such as true or false

Analytics signal:

- If a student writes code but cannot state the expected result, classify the issue as weak output definition.

### 2.3 Constraints

Constraints describe the allowed values and rules.

Examples:

- scores must be between 0 and 100
- capacity cannot be negative
- a list may be empty
- student IDs should be unique

Analytics signal:

- If a student ignores invalid values or empty input, classify the issue as missing constraint handling.

### 2.4 Decomposition

Decomposition breaks a problem into smaller steps.

Example problem:

"Given quiz scores, decide if the class average is passing."

Decomposition:

1. Receive the list of scores.
2. Check whether the list is empty.
3. Add all scores.
4. Count the number of scores.
5. Divide total by count.
6. Compare average with the passing threshold.
7. Return the decision and the average.

Analytics signal:

- If a student jumps from input to final answer with missing intermediate steps, classify the issue as weak decomposition.

### 2.5 Pseudocode

Pseudocode is a readable plan that expresses logic without depending on exact programming syntax.

Effective pseudocode:

```text
receive scores and passing_threshold
if scores is empty:
    return "no scores available"
total = 0
for each score in scores:
    total = total + score
average = total / number of scores
if average >= passing_threshold:
    return "passing"
else:
    return "not passing"
```

The weak version "calculate things and show answer" cannot be traced or graded because it does not expose the decision process.

## 3. Edge Cases

An edge case is a situation at the boundary of normal behavior. Edge cases reveal whether the algorithm is complete.

For score averaging, useful edge cases include:

| Case | Input | Expected Behavior |
| --- | --- | --- |
| empty list | [] | return "no scores available" or ask for data |
| one score | [80] | average is 80 |
| boundary pass | [70], threshold 70 | passing |
| invalid score | [120] | reject or flag invalid score |
| mixed scores | [60, 80, 100] | average is 80 |

Teacher note:

- The system can generate assignment variants by changing the edge-case focus.
- The analytics page can group incorrect answers by failed edge case.

## 4. Tracing

Tracing means manually following the algorithm step by step.

Example trace:

```text
scores = [60, 80, 100]
total starts at 0
after 60, total = 60
after 80, total = 140
after 100, total = 240
count = 3
average = 80
threshold = 70
80 >= 70, so output "passing"
```

Trace tables are useful for individual student analysis because they show where reasoning diverges.

Possible weak-point labels:

- wrong initial value
- skipped loop iteration
- wrong comparison operator
- division by wrong count
- incorrect final branch

## 5. Complexity Reference

Students do not need formal proof in this lecture. They should connect complexity to the number of visited items.

| Pattern | Example | Complexity | Reason |
| --- | --- | --- | --- |
| fixed decision | compare registered count with capacity | O(1) | same number of comparisons |
| single traversal | sum all quiz scores | O(n) | visits each score once |
| nested comparison | compare every student with every other student | O(n^2) | each item is paired with many items |

Common misconception:

- Students may say an algorithm is O(1) because it has one output. The correct question is how much work is required as input size grows.

## 6. Question Seed Bank

### Seed 1: Event Capacity Status

Prompt:

Given room capacity and registered student count, return "fits", "full", or "over capacity".

Required concepts:

- input/output identification
- conditionals
- equality boundary

Expected solution outline:

```text
receive capacity and registered
if registered < capacity, return "fits"
else if registered == capacity, return "full"
else return "over capacity"
```

Rubric:

| Criterion | Points |
| --- | ---: |
| identifies capacity and registered as inputs | 2 |
| defines all three outputs | 2 |
| handles equality correctly | 3 |
| handles greater-than case correctly | 2 |
| includes at least one edge test | 1 |

### Seed 2: Quiz Average Decision

Prompt:

Given a list of scores and a passing threshold, compute the average and return whether the class average is passing.

Required concepts:

- loop traversal
- aggregation
- empty-list handling
- comparison

Expected solution outline:

```text
if scores is empty, return "no scores available"
total = 0
for each score in scores, add score to total
average = total / count of scores
if average >= threshold, return "passing"
else return "not passing"
```

Rubric:

| Criterion | Points |
| --- | ---: |
| handles empty list | 2 |
| sums every score exactly once | 3 |
| divides by correct count | 2 |
| compares average to threshold correctly | 2 |
| explains O(n) complexity | 1 |

### Seed 3: Missing Attendance

Prompt:

Given a list of registered student IDs and a list of attended student IDs, return IDs that registered but did not attend.

Required concepts:

- decomposition
- membership checking
- list traversal
- result collection

Expected solution outline:

```text
missing = empty list
for each id in registered:
    if id is not in attended:
        add id to missing
return missing
```

Rubric:

| Criterion | Points |
| --- | ---: |
| identifies two input lists | 2 |
| checks every registered ID | 3 |
| returns only missing IDs | 3 |
| handles no-missing case | 1 |
| discusses membership-check cost | 1 |

## 7. Analytics Design Notes

Class-level analytics should aggregate by concept and evidence type.

Recommended concept dimensions:

- input_output
- decomposition
- pseudocode
- tracing
- edge_cases
- complexity

Example class analytics summary:

| Concept | Correct Rate | Main Error Pattern | Suggested Action |
| --- | ---: | --- | --- |
| input_output | 72 percent | output category missing | add output contract warm-up |
| edge_cases | 48 percent | equality boundary omitted | add boundary-only practice |
| tracing | 61 percent | loop total updated incorrectly | use trace-table demonstration |
| complexity | 55 percent | O(1) guessed for loops | ask "how many items are visited?" |

## 8. Individual Student Analysis Notes

Student A:

- strength: can identify inputs and outputs
- weak point: misses equality boundary
- evidence: capacity = 30 and registered = 30 returned "over capacity"
- suggested feedback: "Your less-than and greater-than checks work, but equality needs its own branch."
- next practice: two boundary comparison questions

Student B:

- strength: writes readable pseudocode
- weak point: loop tracing
- evidence: trace table skips the second score
- suggested feedback: "Trace every item in the list, one row per item."
- next practice: one aggregation trace before coding

## 9. Lecture Improvement Suggestions

Use these rules for teacher-facing recommendations:

| Analytics Trigger | Improvement Suggestion |
| --- | --- |
| fewer than 60 percent handle equality boundaries | add a short comparison-operator recap |
| fewer than 50 percent provide edge cases | require an edge-case checklist before submission |
| tracing errors appear in more than 30 percent of submissions | add a live trace-table exercise |
| complexity explanations are mostly guesses | use concrete step counting before Big-O notation |

## 10. Suggested Next Lecture

Recommended next lecture if most students pass this unit:

- Data Structures for Storing and Searching Course Data

Recommended remedial lecture if weak points remain:

- Boundary Conditions and Trace Tables

Reason:

- Students need reliable decomposition before data structure selection. If decomposition is weak, later data structure topics may look like memorization instead of design.
