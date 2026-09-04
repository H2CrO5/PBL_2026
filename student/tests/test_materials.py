"""Tests for the Student lecture material viewer API."""

import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.routers.materials import get_student_materials
from db.models import Base, Course, CourseMaterial, Enrollment, Lecture, Student


class StudentMaterialsTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        self.student = Student(
            student_code="s1",
            name="Student One",
            password_hash="not-used",
        )
        other_student = Student(
            student_code="s2",
            name="Student Two",
            password_hash="not-used",
        )
        enrolled_course = Course(
            external_key="course-enrolled",
            title="Enrolled Course",
            term="Spring 2026",
        )
        other_course = Course(
            external_key="course-private",
            title="Other Course",
            term="Spring 2026",
        )
        self.db.add_all([self.student, other_student, enrolled_course, other_course])
        self.db.flush()
        self.db.add_all([
            Enrollment(course_id=enrolled_course.id, student_id=self.student.id),
            Enrollment(course_id=other_course.id, student_id=other_student.id),
        ])
        enrolled_lecture = Lecture(
            course_id=enrolled_course.id,
            external_key="lecture-1",
            lecture_number=1,
            title="Introduction",
        )
        other_lecture = Lecture(
            course_id=other_course.id,
            external_key="lecture-private",
            lecture_number=1,
            title="Private Lecture",
        )
        self.db.add_all([enrolled_lecture, other_lecture])
        self.db.flush()
        self.db.add_all([
            CourseMaterial(
                external_key="material-visible",
                course_id=enrolled_course.id,
                lecture_id=enrolled_lecture.id,
                title="Visible Notes",
                material_type="note",
                content="The full synchronized material content.",
                ingestion_status="ready_lexical",
                student_visible=True,
            ),
            CourseMaterial(
                external_key="material-unpublished",
                course_id=enrolled_course.id,
                lecture_id=enrolled_lecture.id,
                title="Unpublished Answer Key",
                material_type="note",
                content="This is enrolled but must remain hidden.",
                ingestion_status="ready_lexical",
                student_visible=False,
            ),
            CourseMaterial(
                external_key="material-private",
                course_id=other_course.id,
                lecture_id=other_lecture.id,
                title="Private Notes",
                material_type="note",
                content="This must not be visible.",
                ingestion_status="ready_lexical",
                student_visible=True,
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_returns_full_material_grouped_by_enrolled_lecture(self):
        result = get_student_materials(None, self.student, self.db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].external_course_id, "course-enrolled")
        self.assertEqual(result[0].lecture_number, 1)
        self.assertEqual(result[0].lecture_title, "Introduction")
        self.assertEqual(len(result[0].materials), 1)
        self.assertEqual(result[0].materials[0].title, "Visible Notes")
        self.assertEqual(
            result[0].materials[0].content,
            "The full synchronized material content.",
        )

    def test_rejects_course_where_student_is_not_enrolled(self):
        with self.assertRaises(HTTPException) as raised:
            get_student_materials("course-private", self.student, self.db)

        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
