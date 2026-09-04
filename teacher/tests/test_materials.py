"""Tests for Teacher material and lecture management."""

import json
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.routers.materials import create_lecture
from api.schemas.materials import LectureCreateRequest
from db.models import Base, Course, Teacher


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


if __name__ == "__main__":
    unittest.main()
