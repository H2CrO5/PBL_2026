"""Tests for consistent progress and student-visible materials."""

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.routers.assignments import submit_answer
from api.routers.materials import list_student_materials
from api.schemas.assignments import SubmitRequest
from db.models import (
    Assignment,
    Base,
    Course,
    CourseMaterial,
    Enrollment,
    Lecture,
    Student,
    Submission,
)
from services.course_rag import ingest_material, retrieve_course
from services.progress import build_progress_timeline, calculate_progress


class ProgressAndMaterialsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.student = Student(
            student_code="s-progress",
            name="Progress Student",
            password_hash="not-used",
        )
        self.course = Course(
            external_key="course-progress",
            title="Progress Course",
            term="2026",
        )
        self.db.add_all([self.student, self.course])
        self.db.flush()
        self.db.add(Enrollment(
            course_id=self.course.id,
            student_id=self.student.id,
            status="active",
        ))
        self.lecture = Lecture(
            course_id=self.course.id,
            external_key="lecture-progress",
            lecture_number=1,
            title="Progress",
        )
        self.db.add(self.lecture)
        self.db.flush()
        self.assignments = [
            Assignment(
                course_id=self.course.id,
                student_id=self.student.id,
                lecture_id=self.lecture.id,
                topic="Grounding",
                difficulty="medium",
                question_text=f"Question {index}",
                correct_answer="Use evidence",
                explanation="Evidence supports claims",
                rubric='["Uses evidence"]',
                question_type="short_answer",
            )
            for index in range(3)
        ]
        self.db.add_all(self.assignments)
        self.db.flush()
        self.db.add(Submission(
            assignment_id=self.assignments[0].id,
            student_id=self.student.id,
            answer_text="Demo answer",
            is_correct=True,
            score=80,
            feedback="Demo feedback",
            source="seed",
            status="graded",
            submitted_at=datetime.utcnow() - timedelta(days=1),
        ))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    @patch("api.routers.assignments.bedrock_client.invoke_json")
    def test_real_submission_extends_demo_progress_instead_of_resetting_it(self, invoke_json):
        invoke_json.return_value = {
            "score": 60,
            "feedback": "Sufficient",
            "missing_concepts": [],
            "teacher_error_pattern": None,
        }
        before = calculate_progress(self.db, self.student)
        self.assertEqual(before["completed_assignments"], 1)
        self.assertEqual(before["total_assignments"], 3)

        result = submit_answer(
            SubmitRequest(
                assignment_id=self.assignments[1].id,
                answer_text="Evidence supports the claim",
            ),
            self.student,
            self.db,
        )

        self.assertEqual(result.progress_change.completed_before, 1)
        self.assertEqual(result.progress_change.completed_after, 2)
        self.assertEqual(result.progress_change.total_assignments, 3)
        self.assertEqual(result.progress_change.overall_score_before, 80)
        self.assertEqual(result.progress_change.overall_score_after, 70)
        self.db.refresh(self.student)
        self.assertEqual(self.student.total_answered, 2)
        self.assertEqual(self.student.overall_score, 70)

        timeline = build_progress_timeline(self.db, self.student)
        self.assertEqual(len(timeline), 2)
        self.assertEqual(timeline[-1]["completed_assignments"], 2)

    def test_students_see_only_published_materials_in_enrolled_courses(self):
        self.db.add_all([
            CourseMaterial(
                external_key="visible-material",
                course_id=self.course.id,
                lecture_id=self.lecture.id,
                title="Visible",
                material_type="note",
                content="Visible course content",
                student_visible=True,
            ),
            CourseMaterial(
                external_key="private-material",
                course_id=self.course.id,
                lecture_id=self.lecture.id,
                title="Answer key",
                material_type="note",
                content="Private answer key",
                student_visible=False,
            ),
        ])
        self.db.commit()

        result = list_student_materials(None, self.student, self.db)

        self.assertEqual([item.title for item in result], ["Visible"])
        self.assertEqual(result[0].lecture_title, "Progress")

    def test_student_rag_excludes_private_teacher_materials(self):
        visible = CourseMaterial(
            external_key="visible-rag",
            course_id=self.course.id,
            lecture_id=self.lecture.id,
            title="Visible RAG",
            material_type="note",
            content="public grounding evidence",
            student_visible=True,
        )
        private = CourseMaterial(
            external_key="private-rag",
            course_id=self.course.id,
            lecture_id=self.lecture.id,
            title="Private RAG",
            material_type="note",
            content="secret answer key",
            student_visible=False,
        )
        self.db.add_all([visible, private])
        self.db.flush()
        with patch("services.course_rag.BEDROCK_BEARER_TOKEN", ""):
            ingest_material(self.db, visible)
            ingest_material(self.db, private)
            results = retrieve_course(
                self.db,
                self.course.id,
                "secret answer key",
                visible_only=True,
            )

        self.assertTrue(results)
        self.assertEqual({item["source"] for item in results}, {"Visible RAG"})


if __name__ == "__main__":
    unittest.main()
