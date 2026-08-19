"""Build a privacy-scoped Teacher feed from real Student submissions."""

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from db.models import Assignment, Student, Submission


def build_teacher_feed(db: DBSession) -> dict:
    students = db.query(Student).order_by(Student.student_code).all()
    student_rows = []
    class_topics: dict[str, list[Submission]] = defaultdict(list)

    for student in students:
        total_assignments = (
            db.query(Assignment).filter(Assignment.student_id == student.id).count()
        )
        real_submissions = (
            db.query(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .filter(Submission.student_id == student.id, Submission.source == "real")
            .order_by(Submission.submitted_at.desc())
            .all()
        )

        topic_scores: dict[str, list[float]] = defaultdict(list)
        for submission in real_submissions:
            topic = submission.assignment.topic
            topic_scores[topic].append(submission.score)
            class_topics[topic].append(submission)

        topic_averages = {
            topic: sum(scores) / len(scores) for topic, scores in topic_scores.items()
        }
        scores = [submission.score for submission in real_submissions]
        student_rows.append({
            "student_id": student.id,
            "student_code": student.student_code,
            "name": student.name,
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
            "completion_rate": (
                round(100.0 * len(real_submissions) / total_assignments, 1)
                if total_assignments else 0.0
            ),
            "total_assignments": total_assignments,
            "total_submissions": len(real_submissions),
            "strong_topics": sorted(
                topic for topic, average in topic_averages.items() if average >= 80
            ),
            "weak_topics": sorted(
                topic for topic, average in topic_averages.items() if average < 60
            ),
            "recent_submissions": [
                {
                    "submission_id": submission.id,
                    "assignment_id": submission.assignment_id,
                    "topic": submission.assignment.topic,
                    "question_text": submission.assignment.question_text,
                    "answer_text": submission.answer_text,
                    "is_correct": submission.is_correct,
                    "score": submission.score,
                    "feedback": submission.feedback,
                    "submitted_at": submission.submitted_at,
                }
                for submission in real_submissions[:10]
            ],
        })

    topic_metrics = []
    for topic, submissions in class_topics.items():
        incorrect = sum(1 for submission in submissions if not submission.is_correct)
        topic_metrics.append({
            "topic": topic,
            "attempts": len(submissions),
            "incorrect": incorrect,
            "wrong_rate": round(100.0 * incorrect / len(submissions), 1),
        })
    topic_metrics.sort(key=lambda item: (-item["wrong_rate"], item["topic"]))

    return {
        "data_source": "student-real-submissions",
        "generated_at": datetime.now(timezone.utc),
        "students": student_rows,
        "topic_metrics": topic_metrics,
    }
