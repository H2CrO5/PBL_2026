"""Tests for the real-submission Teacher analytics feed."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Assignment, Base, Student, Submission
from services.teacher_analytics import build_teacher_feed
from api.routers.integration import require_teacher_integration


class TeacherAnalyticsFeedTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        student = Student(
            student_code="s1", name="Student One", password_hash="not-used"
        )
        self.db.add(student)
        self.db.flush()
        first = Assignment(
            student_id=student.id,
            topic="RAG citations",
            difficulty="medium",
            question_text="Explain grounding.",
            correct_answer="Use evidence.",
            explanation="Claims need supporting evidence.",
            question_type="short_answer",
        )
        second = Assignment(
            student_id=student.id,
            topic="RAG citations",
            difficulty="medium",
            question_text="Explain citation verification.",
            correct_answer="Check support.",
            explanation="A citation must support the claim.",
            question_type="short_answer",
        )
        self.db.add_all([first, second])
        self.db.flush()
        self.db.add_all([
            Submission(
                assignment_id=first.id,
                student_id=student.id,
                answer_text="Seed answer",
                is_correct=True,
                score=100,
                feedback="Seed feedback",
                source="seed",
            ),
            Submission(
                assignment_id=second.id,
                student_id=student.id,
                answer_text="A link is enough.",
                is_correct=False,
                score=40,
                feedback="Verify that the source supports the claim.",
                source="real",
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_feed_uses_only_real_submissions(self):
        feed = build_teacher_feed(self.db)
        self.assertEqual(feed["data_source"], "student-real-submissions")
        self.assertEqual(len(feed["students"]), 1)
        student = feed["students"][0]
        self.assertEqual(student["average_score"], 40.0)
        self.assertEqual(student["completion_rate"], 50.0)
        self.assertEqual(student["total_submissions"], 1)
        self.assertEqual(student["weak_topics"], ["RAG citations"])
        self.assertEqual(len(student["recent_submissions"]), 1)
        self.assertEqual(feed["topic_metrics"][0]["wrong_rate"], 100.0)

    def test_integration_token_is_required(self):
        with patch("api.routers.integration.TEACHER_INTEGRATION_TOKEN", "expected"):
            require_teacher_integration("expected")
            with self.assertRaises(HTTPException) as raised:
                require_teacher_integration("wrong")
            self.assertEqual(raised.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
