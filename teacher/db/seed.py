"""Seed the teacher module with demo courses, materials, analytics, and students."""

import json
import sys
from pathlib import Path

import bcrypt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal, create_tables
from db.models import (
    ConceptMetric,
    Course,
    Lecture,
    Material,
    QuestionSeed,
    StudentProfile,
    Teacher,
)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


BASE_DIR = Path(__file__).resolve().parent.parent


LECTURES = [
    {
        "number": 1,
        "title": "Algorithmic Thinking and Problem Decomposition",
        "group_dir": "lecture_group_01_algorithmic_thinking",
        "objectives": [
            "Identify inputs, outputs, constraints, and edge cases",
            "Break a programming problem into ordered subproblems",
            "Trace an algorithm and explain simple complexity",
        ],
        "materials": [
            {
                "title": "Slides: Algorithmic Thinking",
                "type": "slide",
                "file": "slides_algorithmic_thinking.md",
            },
            {
                "title": "Reference: Algorithmic Thinking",
                "type": "book",
                "file": "reference_algorithmic_thinking.md",
            },
        ],
    },
    {
        "number": 2,
        "title": "Data Structures and Complexity",
        "group_dir": "lecture_group_02_data_structures_complexity",
        "objectives": [
            "Choose data structures based on required operations",
            "Connect lookup, traversal, stack, queue, and set behavior to complexity",
            "Justify data structure choices in teacher dashboard scenarios",
        ],
        "materials": [
            {
                "title": "Slides: Data Structures and Complexity",
                "type": "slide",
                "file": "slides_data_structures_complexity.md",
            },
            {
                "title": "Reference: Data Structures and Complexity",
                "type": "book",
                "file": "reference_data_structures_complexity.md",
            },
        ],
    },
]

STUDENTS = [
    {
        "student_code": "s2024001",
        "name": "Tanaka Taro",
        "average_score": 76,
        "completion_rate": 92,
        "strong_topics": ["Input/output identification", "Pseudocode"],
        "weak_topics": ["Edge cases", "Trace tables"],
        "recommended_action": "Give one trace-table practice question before the next lecture.",
    },
    {
        "student_code": "s2024002",
        "name": "Suzuki Hanako",
        "average_score": 58,
        "completion_rate": 78,
        "strong_topics": ["Loop traversal"],
        "weak_topics": ["Empty-list handling", "Boundary comparison"],
        "recommended_action": "Provide a supportive quiz-average problem with edge cases.",
    },
    {
        "student_code": "s2024003",
        "name": "Sato Kenji",
        "average_score": 84,
        "completion_rate": 100,
        "strong_topics": ["Dictionary lookup", "Set membership"],
        "weak_topics": ["Stack vs queue"],
        "recommended_action": "Ask the student to explain stack/queue differences to a peer.",
    },
    {
        "student_code": "s2024004",
        "name": "Kim Mina",
        "average_score": 49,
        "completion_rate": 66,
        "strong_topics": ["Basic list traversal"],
        "weak_topics": ["Decomposition", "Complexity intuition", "Dictionary use"],
        "recommended_action": "Schedule one-on-one follow-up and assign operation-first data-structure practice.",
    },
]

CONCEPTS = [
    {
        "concept": "Edge-case handling",
        "wrong_rate": 62,
        "misconception": "Students solve the normal case but miss empty input and equality boundaries.",
        "recommended_focus": "Use trace tables to compare normal cases and edge cases.",
    },
    {
        "concept": "Problem decomposition",
        "wrong_rate": 54,
        "misconception": "Students jump directly to code before defining inputs, outputs, and intermediate steps.",
        "recommended_focus": "Have students rewrite a raw problem into inputs, outputs, rules, and edge cases.",
    },
    {
        "concept": "Data-structure selection",
        "wrong_rate": 47,
        "misconception": "Students overuse lists instead of choosing dictionaries, sets, stacks, or queues by operation.",
        "recommended_focus": "Run an operation-first activity: lookup, membership, undo, and arrival-order processing.",
    },
    {
        "concept": "Complexity intuition",
        "wrong_rate": 29,
        "misconception": "Students describe complexity from output size instead of how work grows with input.",
        "recommended_focus": "Compare fixed decision, single traversal, and nested comparison examples.",
    },
]

QUESTION_SEEDS = [
    {
        "lecture_number": 1,
        "title": "Event capacity status",
        "target_concept": "Edge-case handling",
        "seed_type": "required",
        "difficulty": "medium",
        "question_text": (
            "Given a room capacity and the current number of registered students, "
            "return full, available, or overbooked. Include the equality boundary."
        ),
        "expected_answer": (
            "Compare registered students against capacity: equal means full, below means available, "
            "and above means overbooked."
        ),
        "rubric": [
            "Identifies capacity and registered count as inputs",
            "Handles equality as the full case",
            "Separates available and overbooked cases correctly",
        ],
        "notes": "Required checkpoint because many students miss equality boundaries.",
    },
    {
        "lecture_number": 1,
        "title": "Quiz average trace",
        "target_concept": "Problem decomposition",
        "seed_type": "base",
        "difficulty": "easy",
        "question_text": (
            "Decompose a quiz-average problem into inputs, processing steps, output, and one edge case."
        ),
        "expected_answer": (
            "Inputs are quiz scores; processing sums scores and divides by count; output is average; "
            "an edge case is an empty score list."
        ),
        "rubric": [
            "Names input, process, output, and edge case",
            "Keeps decomposition separate from code syntax",
            "Explains why empty input needs a rule",
        ],
        "notes": "Good base question for lower-confidence students.",
    },
    {
        "lecture_number": 2,
        "title": "Choose the right structure",
        "target_concept": "Data-structure selection",
        "seed_type": "required",
        "difficulty": "medium",
        "question_text": (
            "For student lookup by ID, assignment processing in arrival order, and undoing the most "
            "recent material edit, choose suitable data structures and justify each choice."
        ),
        "expected_answer": (
            "Use a dictionary for ID lookup, a queue for arrival-order processing, and a stack for undo."
        ),
        "rubric": [
            "Matches each workflow to an operation",
            "Chooses dictionary, queue, and stack appropriately",
            "Justifies choices using lookup/order/most-recent behavior",
        ],
        "notes": "Required because this maps directly to the teacher dashboard scenario.",
    },
    {
        "lecture_number": 2,
        "title": "Complexity explanation rubric",
        "target_concept": "Complexity intuition",
        "seed_type": "rubric_seed",
        "difficulty": "hard",
        "question_text": (
            "Explain why checking membership in a set can be preferable to repeated list scanning "
            "when validating submitted student IDs."
        ),
        "expected_answer": (
            "A set supports fast membership checks, while repeated list scans grow with the list size "
            "for each check."
        ),
        "rubric": [
            "Compares operations rather than naming structures only",
            "Mentions growth of repeated list scanning",
            "Connects the explanation to submitted student ID validation",
        ],
        "notes": "Use as a rubric seed for generated variants.",
    },
]


def seed():
    """Populate demo teacher data."""
    create_tables()
    db = SessionLocal()

    try:
        if db.query(Teacher).count() > 0:
            print("Teacher database already seeded. Skipping.")
            return

        teacher = Teacher(
            teacher_code="t2024001",
            name="東北一郎",
            password_hash=_hash_password("demo123"),
        )
        db.add(teacher)
        db.flush()

        course = Course(
            teacher_id=teacher.id,
            external_key="course-generative-ai-2026",
            title="Generative AI Systems for Education",
            term="Spring 2026",
        )
        db.add(course)
        db.flush()

        lectures_by_number = {}

        for lecture_data in LECTURES:
            lecture = Lecture(
                course_id=course.id,
                lecture_number=lecture_data["number"],
                title=lecture_data["title"],
                learning_objectives=json.dumps(lecture_data["objectives"]),
            )
            db.add(lecture)
            db.flush()
            lectures_by_number[lecture_data["number"]] = lecture

            for material_data in lecture_data["materials"]:
                source_path = BASE_DIR / "materials" / lecture_data["group_dir"] / material_data["file"]
                content = source_path.read_text(encoding="utf-8")
                material = Material(
                    external_key=f"material-{lecture_data['number']}-{material_data['file']}",
                    course_id=course.id,
                    lecture_id=lecture.id,
                    title=material_data["title"],
                    material_type=material_data["type"],
                    source_path=str(source_path.relative_to(BASE_DIR)),
                    content=content,
                    ingestion_status="local_only",
                    student_visible=True,
                )
                db.add(material)

        for student_data in STUDENTS:
            db.add(StudentProfile(
                course_id=course.id,
                student_code=student_data["student_code"],
                name=student_data["name"],
                average_score=student_data["average_score"],
                completion_rate=student_data["completion_rate"],
                strong_topics=json.dumps(student_data["strong_topics"]),
                weak_topics=json.dumps(student_data["weak_topics"]),
                recommended_action=student_data["recommended_action"],
            ))

        for concept_data in CONCEPTS:
            db.add(ConceptMetric(course_id=course.id, **concept_data))

        for seed_data in QUESTION_SEEDS:
            lecture = lectures_by_number[seed_data["lecture_number"]]
            db.add(QuestionSeed(
                course_id=course.id,
                lecture_id=lecture.id,
                title=seed_data["title"],
                target_concept=seed_data["target_concept"],
                seed_type=seed_data["seed_type"],
                difficulty=seed_data["difficulty"],
                question_text=seed_data["question_text"],
                expected_answer=seed_data["expected_answer"],
                rubric=json.dumps(seed_data["rubric"], ensure_ascii=False),
                notes=seed_data["notes"],
            ))

        db.commit()
        print("Seeded teacher demo data.")
        print("Demo teacher account: t2024001 / demo123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
