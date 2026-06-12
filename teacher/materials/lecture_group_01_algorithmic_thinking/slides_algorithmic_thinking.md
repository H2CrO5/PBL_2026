# Slide Material: Algorithmic Thinking and Problem Decomposition

Material ID: TG01-SLIDES-ALG-THINKING
Lecture Group: TG01 Algorithmic Thinking
Material Type: slide-style
Estimated Duration: 75 minutes
Teacher Workflows Supported: material review, question seed authoring, generation context review, class analytics, weak-point analysis, lecture improvement suggestions

## Material Tags

- problem decomposition
- input and output
- pseudocode
- tracing
- edge cases
- complexity intuition
- debugging reasoning

## Slide 1: Teaching Goal

Students should learn how to turn an unclear problem statement into a precise algorithm before writing code.

By the end of the lecture, students should be able to:

- identify inputs, outputs, and constraints
- split a problem into ordered subproblems
- write clear pseudocode
- trace an algorithm with sample data
- explain simple time complexity using O(1), O(n), and O(n^2)
- name at least two edge cases before coding

## Slide 2: Opening Scenario

Scenario: A campus event team needs to decide whether a classroom can hold all registered students.

Raw request:

"Tell us if the event can fit in the assigned room."

Computational version:

- input: room capacity, number of registered students, number of waitlisted students
- output: one of "fits", "full", or "over capacity"
- constraint: capacity and counts are non-negative integers
- edge cases: capacity is 0, registered count equals capacity, waitlist is larger than capacity

Teacher prompt:

- Ask students what information is missing.
- Ask which output categories are useful for a teacher or event organizer.

## Slide 3: From Problem Statement to Algorithm

A reliable algorithm starts with five questions:

1. What data do I receive?
2. What result must I produce?
3. What rules decide the result?
4. What steps transform input into output?
5. What cases might break the simple version?

Class activity:

- Give students a one-sentence task.
- Have them rewrite it as inputs, outputs, rules, and edge cases.

## Slide 4: Decomposition Pattern

Use this pattern for early programming tasks:

1. Read or receive input.
2. Validate the input.
3. Compute intermediate values.
4. Decide which branch applies.
5. Return or display the result.
6. Test normal cases and edge cases.

Example:

```text
if registered < capacity:
    status = "fits"
else if registered == capacity:
    status = "full"
else:
    status = "over capacity"
```

Common weak point:

- Students often start coding before they know the expected output categories.

## Slide 5: Pseudocode Rules

Good pseudocode is:

- specific enough to trace
- language-neutral enough to discuss
- ordered from first step to last step
- explicit about decisions
- explicit about repeated work

Weak pseudocode:

```text
check the room
print result
```

Better pseudocode:

```text
receive capacity and registered count
if registered is less than capacity, output "fits"
if registered equals capacity, output "full"
if registered is greater than capacity, output "over capacity"
```

## Slide 6: Tracing an Algorithm

Trace table for the room capacity example:

| capacity | registered | comparison | output |
| --- | ---: | --- | --- |
| 30 | 25 | 25 < 30 | fits |
| 30 | 30 | 30 == 30 | full |
| 30 | 35 | 35 > 30 | over capacity |

Teacher prompt:

- Ask students to explain each row aloud.
- Ask students to find the first row that tests an edge condition.

## Slide 7: Edge Case Checklist

Before coding, check:

- minimum values
- maximum values
- empty input
- equal boundary values
- duplicate values
- invalid values
- one-item input
- already sorted or already solved input

Example edge cases:

- capacity = 0, registered = 0
- capacity = 30, registered = 30
- capacity = 30, registered = 31

## Slide 8: Complexity Intuition

Complexity describes how work grows as input grows.

- O(1): the number of steps stays about the same.
- O(n): the number of steps grows with the number of items.
- O(n^2): nested comparison causes work to grow much faster.

Teacher analogy:

- Checking one classroom capacity is O(1).
- Checking every classroom in a list is O(n).
- Comparing every student with every other student is O(n^2).

## Slide 9: Mini Activity

Task:

"Given a list of quiz scores, decide whether the class average is passing."

Students should produce:

- inputs: list of scores, passing threshold
- output: pass status and average
- steps: sum scores, count scores, divide, compare with threshold
- edge cases: empty list, threshold equals average, score outside valid range

Expected complexity:

- O(n), because each score must be visited once.

## Slide 10: Question Seed Candidates

Seed A: Basic

- Prompt: Given room capacity and registered count, output the event status.
- Concepts: conditionals, boundary testing
- Difficulty: easy
- Expected answer: correct branch for less than, equal, and greater than capacity
- Rubric: 40 percent conditions, 30 percent edge cases, 20 percent clarity, 10 percent variable naming

Seed B: Intermediate

- Prompt: Given a list of quiz scores, compute the average and decide whether it meets a threshold.
- Concepts: loops, aggregation, division, conditionals
- Difficulty: medium
- Expected answer: sum all scores, divide by count, compare with threshold
- Rubric: 35 percent aggregation, 25 percent handling empty input, 25 percent comparison logic, 15 percent explanation

Seed C: Challenge

- Prompt: Given two attendance lists, find students who registered but did not attend.
- Concepts: decomposition, list comparison, membership test, complexity
- Difficulty: medium to hard
- Expected answer: compare registered students against attended students and return missing names
- Rubric: 30 percent decomposition, 30 percent correct membership logic, 20 percent complexity discussion, 20 percent edge cases

## Slide 11: Class Analytics Hooks

Track these signals after students submit work:

- percent of students who identify all inputs and outputs
- percent of students who include boundary tests
- percent of students who confuse equality with less-than or greater-than checks
- percent of students who write pseudocode before code
- percent of students who can trace at least two rows correctly
- average score by concept tag

Suggested dashboard metrics:

| Metric | Healthy Signal | Warning Signal |
| --- | --- | --- |
| Input/output identification | above 80 percent correct | below 60 percent correct |
| Edge case coverage | at least 2 valid cases per answer | no boundary cases |
| Trace accuracy | most rows match expected output | repeated branch confusion |
| Complexity explanation | uses O(n) for list traversal | calls every task O(1) |

## Slide 12: Weak-Point Map

| Weak Point | Observable Evidence | Suggested Intervention |
| --- | --- | --- |
| unclear output definition | answer has code but no stated result | require a one-line output contract |
| boundary confusion | fails when value equals threshold | run equality-only examples |
| missing edge cases | tests only normal values | use edge case checklist before coding |
| tracing errors | trace table does not match pseudocode | have students trace with a partner |
| complexity guessing | uses complexity terms without reason | ask "how many items are visited?" |

## Slide 13: Lecture Improvement Suggestions

If analytics show low input/output identification:

- add a 5-minute warm-up where students mark nouns as data and verbs as actions
- show two examples where missing output categories create wrong code

If analytics show weak edge-case coverage:

- add an edge-case checkpoint before the coding activity
- require one boundary test in every assignment

If analytics show complexity confusion:

- use physical counting examples before notation
- compare one lookup, one loop, and one nested loop side by side

## Slide 14: Next Lecture Bridge

Bridge to the next lecture group:

- Decomposition tells us what steps are needed.
- Data structures help us choose how to store and access the data for those steps.
- The next lecture compares lists, sets, dictionaries, stacks, and queues.

Exit ticket:

- "Name one problem where a list is enough and one problem where a faster membership check would help."
