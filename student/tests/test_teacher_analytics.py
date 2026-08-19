"""Tests for the real-submission Teacher analytics feed."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Assignment, Base, ChatMessage, Course, CourseMaterial, Student, Submission
from services.teacher_analytics import build_teacher_feed
from api.routers.integration import (
    override_grade,
    assignment_analytics,
    publish_assignment,
    require_teacher_integration,
    sync_material,
)
from api.schemas.integration import (
    AssignmentPublishRequest,
    GradeOverrideRequest,
    MaterialSyncRequest,
)
from api.schemas.assignments import SubmitRequest
from api.routers.assignments import submit_answer
from api.routers.students import _memory


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
        self.db.add(ChatMessage(
            student_id=student.id,
            role="user",
            content="How do I verify a citation?",
        ))
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
        self.assertEqual(student["chat_summary"], ["How do I verify a citation?"])
        self.assertEqual(feed["topic_metrics"][0]["wrong_rate"], 100.0)
        self.assertEqual(len(feed["score_trend"]), 1)

    def test_student_memory_uses_real_latest_attempts(self):
        student = self.db.query(Student).filter(Student.student_code == "s1").one()
        memory = _memory(self.db, student, None)
        self.assertEqual(memory.overall_score, 40.0)
        self.assertEqual(memory.weak_topics, ["RAG citations"])
        self.assertEqual(memory.concept_mastery[0].evidence, [2])

    def test_integration_token_is_required(self):
        with patch("api.routers.integration.TEACHER_INTEGRATION_TOKEN", "expected"):
            require_teacher_integration("expected")
            with self.assertRaises(HTTPException) as raised:
                require_teacher_integration("wrong")
            self.assertEqual(raised.exception.status_code, 401)

    def test_assignment_publish_is_idempotent(self):
        request = AssignmentPublishRequest(
            external_assignment_id="asg-1",
            external_course_id="course-1",
            course_title="Course One",
            lecture_external_id="lecture-1",
            lecture_number=1,
            lecture_title="Introduction",
            title="Grounding checkpoint",
            target_concept="RAG grounding",
            difficulty="balanced",
            question_text="Explain grounding.",
            correct_answer="Use retrieved evidence.",
            explanation="Ground claims in evidence.",
            rubric=["Mentions evidence"],
            max_attempts=2,
        )
        first = publish_assignment(request, self.db)
        second = publish_assignment(request, self.db)
        self.assertEqual(first.created, 1)
        self.assertEqual(second.already_present, 1)
        assignment = self.db.query(Assignment).filter(
            Assignment.external_key == "asg-1:s1"
        ).one()
        self.assertEqual(assignment.max_attempts, 2)
        course = self.db.query(Course).filter(Course.id == assignment.course_id).one()
        self.assertEqual(course.external_key, "course-1")

    def test_assignment_analytics_uses_real_submission(self):
        request = AssignmentPublishRequest(
            external_assignment_id="asg-analytics",
            external_course_id="course-analytics",
            course_title="Analytics Course",
            lecture_external_id="lecture-analytics",
            lecture_number=1,
            lecture_title="Analytics",
            title="Analytics checkpoint",
            target_concept="Evidence",
            difficulty="balanced",
            question_text="Explain evidence.",
            correct_answer="Use sources.",
            explanation="Use sources.",
            rubric=["Uses sources"],
        )
        publish_assignment(request, self.db)
        assignment = self.db.query(Assignment).filter(
            Assignment.external_key == "asg-analytics:s1"
        ).one()
        self.db.add(Submission(
            assignment_id=assignment.id,
            student_id=assignment.student_id,
            answer_text="Sources support claims.",
            is_correct=True,
            score=90,
            feedback="Good",
            source="real",
        ))
        self.db.commit()
        result = assignment_analytics("asg-analytics", self.db)
        self.assertEqual(result.total_assigned, 1)
        self.assertEqual(result.total_submitted, 1)
        self.assertEqual(result.average_score, 90.0)

    def test_material_sync_builds_course_scoped_chunks(self):
        request = MaterialSyncRequest(
            external_material_id="mat-1",
            external_course_id="course-1",
            course_title="Course One",
            lecture_external_id="lecture-1",
            lecture_number=1,
            lecture_title="Introduction",
            title="Grounding notes",
            material_type="note",
            content="Ground every important claim in retrieved course evidence. " * 20,
        )
        with patch("services.course_rag.BEDROCK_BEARER_TOKEN", ""):
            result = sync_material(request, self.db)
        self.assertEqual(result.ingestion_status, "ready_lexical")
        self.assertGreater(result.chunk_count, 0)
        self.assertEqual(self.db.query(CourseMaterial).count(), 1)

    def test_grade_override_preserves_auto_grade(self):
        publish = AssignmentPublishRequest(
            external_assignment_id="asg-override",
            external_course_id="course-override",
            course_title="Override Course",
            lecture_external_id="lecture-override",
            lecture_number=1,
            lecture_title="Review",
            title="Review question",
            target_concept="Review",
            difficulty="balanced",
            question_text="Explain.",
            correct_answer="Explanation.",
            explanation="Explanation.",
            rubric=["Explains"],
        )
        publish_assignment(publish, self.db)
        assignment = self.db.query(Assignment).filter(
            Assignment.external_key == "asg-override:s1"
        ).one()
        submission = Submission(
            assignment_id=assignment.id,
            student_id=assignment.student_id,
            answer_text="Answer",
            is_correct=False,
            score=40,
            feedback="Automatic feedback",
            source="real",
        )
        self.db.add(submission)
        self.db.commit()
        result = override_grade(
            submission.id,
            GradeOverrideRequest(
                external_course_id="course-override",
                score=75,
                feedback="Teacher correction",
            ),
            self.db,
        )
        self.assertEqual(result.grading_source, "teacher_override")
        self.db.refresh(submission)
        self.assertEqual(submission.auto_score, 40)
        self.assertEqual(submission.score, 75)

    @patch("api.routers.assignments.bedrock_client.invoke_json")
    def test_grading_failure_saves_answer_without_consuming_retry(self, invoke_json):
        invoke_json.side_effect = RuntimeError("provider unavailable")
        student = self.db.query(Student).filter(Student.student_code == "s1").one()
        assignment = Assignment(
            student_id=student.id,
            topic="Failure handling",
            difficulty="medium",
            question_text="Explain retry safety.",
            correct_answer="Persist before provider call.",
            explanation="The answer must not be lost.",
            question_type="short_answer",
            max_attempts=1,
        )
        self.db.add(assignment)
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            submit_answer(
                SubmitRequest(assignment_id=assignment.id, answer_text="My answer"),
                student,
                self.db,
            )
        self.assertEqual(raised.exception.status_code, 502)
        saved = self.db.query(Submission).filter(
            Submission.assignment_id == assignment.id
        ).one()
        self.assertEqual(saved.status, "grading_failed")
        self.assertEqual(saved.answer_text, "My answer")


if __name__ == "__main__":
    unittest.main()
