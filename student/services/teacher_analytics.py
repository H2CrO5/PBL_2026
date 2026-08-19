"""Build a privacy-scoped Teacher feed from real Student submissions."""

from collections import defaultdict
from datetime import datetime, timezone
import json

from sqlalchemy.orm import Session as DBSession

from db.models import Assignment, ChatMessage, Course, Enrollment, Student, Submission
from services.progress import latest_attempts


def build_teacher_feed(db: DBSession, external_course_id: str | None = None) -> dict:
    course = None
    if external_course_id:
        course = db.query(Course).filter(Course.external_key == external_course_id).first()
        if course is None:
            return {
                "data_source": "student-real-submissions",
                "generated_at": datetime.now(timezone.utc),
                "external_course_id": external_course_id,
                "students": [],
                "topic_metrics": [],
            }
        students = (
            db.query(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .filter(Enrollment.course_id == course.id, Enrollment.status == "active")
            .order_by(Student.student_code)
            .all()
        )
    else:
        students = db.query(Student).order_by(Student.student_code).all()
    student_rows = []
    class_topics: dict[str, list[Submission]] = defaultdict(list)
    class_days: dict[str, list[float]] = defaultdict(list)

    for student in students:
        total_assignments = (
            db.query(Assignment).filter(
                Assignment.student_id == student.id,
                *([Assignment.course_id == course.id] if course else []),
            ).count()
        )
        all_real_submissions = (
            db.query(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .filter(
                Submission.student_id == student.id,
                Submission.source == "real",
                *([Assignment.course_id == course.id] if course else []),
            )
            .order_by(Submission.submitted_at.desc())
            .all()
        )
        real_submissions = latest_attempts(all_real_submissions)

        topic_scores: dict[str, list[float]] = defaultdict(list)
        for submission in real_submissions:
            topic = submission.assignment.topic
            topic_scores[topic].append(submission.score)
            class_topics[topic].append(submission)
            class_days[submission.submitted_at.strftime("%Y-%m-%d")].append(submission.score)

        recent_questions = (
            db.query(ChatMessage)
            .filter(ChatMessage.student_id == student.id, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc())
            .limit(5)
            .all()
        )

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
                    "external_assignment_id": submission.assignment.external_key,
                    "topic": submission.assignment.topic,
                    "question_text": submission.assignment.question_text,
                    "answer_text": submission.answer_text,
                    "is_correct": submission.is_correct,
                    "score": submission.score,
                    "feedback": submission.feedback,
                    "attempt_number": submission.attempt_number,
                    "grading_source": submission.grading_source,
                    "missing_concepts": json.loads(submission.missing_concepts or "[]"),
                    "teacher_error_pattern": submission.teacher_error_pattern,
                    "submitted_at": submission.submitted_at,
                }
                for submission in real_submissions[:10]
            ],
            "chat_summary": [message.content[:240] for message in recent_questions],
        })

    topic_metrics = []
    for topic, submissions in class_topics.items():
        incorrect = sum(1 for submission in submissions if not submission.is_correct)
        patterns = [
            submission.teacher_error_pattern
            for submission in submissions
            if submission.teacher_error_pattern
        ]
        topic_metrics.append({
            "topic": topic,
            "attempts": len(submissions),
            "incorrect": incorrect,
            "wrong_rate": round(100.0 * incorrect / len(submissions), 1),
            "common_error_patterns": list(dict.fromkeys(patterns))[:3],
        })
    topic_metrics.sort(key=lambda item: (-item["wrong_rate"], item["topic"]))
    score_trend = [
        {
            "date": date,
            "average_score": round(sum(scores) / len(scores), 1),
            "submissions": len(scores),
        }
        for date, scores in sorted(class_days.items())
    ]

    return {
        "data_source": "student-real-submissions",
        "generated_at": datetime.now(timezone.utc),
        "external_course_id": external_course_id,
        "students": student_rows,
        "topic_metrics": topic_metrics,
        "score_trend": score_trend,
    }
