"""Build student memory context for adaptive assignment generation."""

import json
from collections import defaultdict

from sqlalchemy.orm import Session as DBSession

from db.models import Assignment, Student, Submission


def build_student_memory(db: DBSession, student: Student) -> dict:
    """Analyze student's history and build a context dict for prompt injection.

    Returns:
        dict with keys:
            - overall_score: float
            - topic_scores: dict[str, float]  (topic -> average score)
            - weak_topics: list[str]           (avg < 60)
            - strong_topics: list[str]         (avg >= 80)
            - suggested_difficulty: str        (easy / medium / hard)
            - suggested_topic: str             (lowest-scoring topic)
            - recent_questions: list[str]      (last 10 question texts)
    """
    # Fetch all submissions with their assignments
    submissions = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    # Compute topic-level scores
    topic_scores_raw: dict[str, list[float]] = defaultdict(list)
    for sub in submissions:
        topic_scores_raw[sub.assignment.topic].append(sub.score)

    topic_scores = {
        topic: round(sum(scores) / len(scores), 1)
        for topic, scores in topic_scores_raw.items()
    }

    # Identify weak and strong topics
    weak = [t for t, s in topic_scores.items() if s < 60]
    strong = [t for t, s in topic_scores.items() if s >= 80]

    # Suggest difficulty based on overall score
    overall = student.overall_score
    if overall < 50:
        difficulty = "easy"
    elif overall < 75:
        difficulty = "medium"
    else:
        difficulty = "hard"

    # Suggest topic: pick the lowest-scoring topic, or default
    all_topics = ["Python基礎", "データ構造", "アルゴリズム"]
    if topic_scores:
        suggested_topic = min(topic_scores, key=topic_scores.get)
    else:
        suggested_topic = all_topics[0]

    # Recent questions for dedup
    recent_questions = [
        sub.assignment.question_text
        for sub in submissions[:10]
    ]

    return {
        "overall_score": overall,
        "topic_scores": topic_scores,
        "weak_topics": weak,
        "strong_topics": strong,
        "suggested_difficulty": difficulty,
        "suggested_topic": suggested_topic,
        "recent_questions": recent_questions,
    }
