"""Tests for Teacher material and lecture management."""

import json
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.routers.materials import (
    _sync_payload,
    create_lecture,
    create_material,
    update_material_audience,
)
from api.schemas.materials import (
    LectureCreateRequest,
    MaterialAudienceRequest,
    MaterialCreateRequest,
)
from db.models import Base, Course, Lecture, Material, Teacher


class LectureManagementTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.teacher = Teacher(
            teacher_code="teacher-test",
            name="Test Teacher",
            password_hash="not-used",
        )
        self.session.add(self.teacher)
        self.session.flush()
        self.course = Course(
            external_key="course-test",
            teacher_id=self.teacher.id,
            title="Test Course",
            term="2026",
        )
        self.session.add(self.course)
        self.session.commit()

    def _lecture(self):
        lecture = Lecture(
            course_id=self.course.id,
            lecture_number=1,
            title="Grounded Generation",
            learning_objectives="[]",
        )
        self.session.add(lecture)
        self.session.commit()
        return lecture

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _request(self, **overrides):
        values = {
            "course_id": self.course.id,
            "lecture_number": 1,
            "title": "  Grounded Generation  ",
            "learning_objectives": ["  Explain grounding  ", "Cite evidence"],
        }
        values.update(overrides)
        return LectureCreateRequest(**values)

    def test_teacher_can_create_lecture_for_owned_course(self):
        lecture = create_lecture(self._request(), self.teacher, self.session)

        self.assertEqual(lecture.lecture_number, 1)
        self.assertEqual(lecture.title, "Grounded Generation")
        self.assertEqual(
            lecture.learning_objectives,
            ["Explain grounding", "Cite evidence"],
        )

        stored = self.session.get(Course, self.course.id).lectures[0]
        self.assertEqual(json.loads(stored.learning_objectives), lecture.learning_objectives)

    def test_duplicate_lecture_number_is_rejected(self):
        create_lecture(self._request(), self.teacher, self.session)

        with self.assertRaises(HTTPException) as raised:
            create_lecture(
                self._request(title="Another lecture"),
                self.teacher,
                self.session,
            )

        self.assertEqual(raised.exception.status_code, 409)

    def test_teacher_cannot_create_lecture_for_another_teacher_course(self):
        other_teacher = Teacher(
            teacher_code="teacher-other",
            name="Other Teacher",
            password_hash="not-used",
        )
        self.session.add(other_teacher)
        self.session.commit()

        with self.assertRaises(HTTPException) as raised:
            create_lecture(self._request(), other_teacher, self.session)

        self.assertEqual(raised.exception.status_code, 404)

    def test_blank_learning_objectives_are_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            create_lecture(
                self._request(learning_objectives=[" ", ""]),
                self.teacher,
                self.session,
            )

        self.assertEqual(raised.exception.status_code, 422)

    def test_manual_material_defaults_to_teacher_only(self):
        lecture = self._lecture()
        result = create_material(
            MaterialCreateRequest(
                course_id=self.course.id,
                lecture_id=lecture.id,
                title="Internal checklist",
                material_type="note",
                content="Only teachers should read this.",
            ),
            self.teacher,
            self.session,
        )

        self.assertEqual(result.audience, "teacher")
        stored = self.session.query(Material).filter(Material.id == result.id).one()
        self.assertEqual(stored.audience, "teacher")

    def test_student_sync_payload_removes_labeled_teacher_sections(self):
        lecture = self._lecture()
        material = Material(
            external_key="course-test:material-public",
            course_id=self.course.id,
            lecture_id=lecture.id,
            title="Lecture slides",
            material_type="slide",
            audience="student",
            content=(
                "# Topic\nStudent explanation.\n\n"
                "Teacher note: Check the rubric.\nNever show this sentence.\n\n"
                "# Practice\nStudent activity."
            ),
        )
        self.session.add(material)
        self.session.commit()

        payload = _sync_payload(material)

        self.assertEqual(payload["audience"], "student")
        self.assertIn("Student explanation.", payload["content"])
        self.assertIn("Student activity.", payload["content"])
        self.assertNotIn("Teacher note", payload["content"])
        self.assertNotIn("Never show", payload["content"])

    def test_teacher_can_change_existing_material_visibility(self):
        lecture = self._lecture()
        material = Material(
            external_key="course-test:material-private",
            course_id=self.course.id,
            lecture_id=lecture.id,
            title="Internal checklist",
            material_type="note",
            audience="teacher",
            content="Student-safe checklist.",
        )
        self.session.add(material)
        self.session.commit()

        result = update_material_audience(
            material.id,
            MaterialAudienceRequest(audience="student"),
            self.teacher,
            self.session,
        )

        self.assertEqual(result.audience, "student")
        self.assertEqual(result.ingestion_status, "local_only")


if __name__ == "__main__":
    unittest.main()
