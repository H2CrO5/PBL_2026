"""SQLAlchemy ORM models for the teacher education system."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="teacher")
    courses = relationship("Course", back_populates="teacher")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    token = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    teacher = relationship("Teacher", back_populates="sessions")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_key = Column(Text, unique=True, nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    title = Column(Text, nullable=False)
    term = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="courses")
    lectures = relationship("Lecture", back_populates="course")
    students = relationship("StudentProfile", back_populates="course")
    question_seeds = relationship("QuestionSeed", back_populates="course")
    published_assignments = relationship("PublishedAssignment", back_populates="course")


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lecture_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    learning_objectives = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="lectures")
    materials = relationship("Material", back_populates="lecture")
    question_seeds = relationship("QuestionSeed", back_populates="lecture")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_key = Column(Text, unique=True, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    title = Column(Text, nullable=False)
    material_type = Column(Text, nullable=False)  # slide / book / note
    source_path = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    ingestion_status = Column(Text, default="ready")
    created_at = Column(DateTime, default=datetime.utcnow)

    lecture = relationship("Lecture", back_populates="materials")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_code = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    average_score = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    strong_topics = Column(Text, default="[]")
    weak_topics = Column(Text, default="[]")
    recommended_action = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="students")


class ConceptMetric(Base):
    __tablename__ = "concept_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    concept = Column(Text, nullable=False)
    wrong_rate = Column(Float, nullable=False)
    misconception = Column(Text, nullable=False)
    recommended_focus = Column(Text, nullable=False)


class QuestionSeed(Base):
    __tablename__ = "question_seeds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=True)
    title = Column(Text, nullable=False)
    target_concept = Column(Text, nullable=False)
    seed_type = Column(Text, nullable=False)  # base / required / rubric_seed
    difficulty = Column(Text, nullable=False)
    question_text = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)
    rubric = Column(Text, nullable=False)  # JSON list
    points = Column(Float, nullable=False, default=100.0)
    max_attempts = Column(Integer, nullable=False, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="question_seeds")
    lecture = relationship("Lecture", back_populates="question_seeds")


class PublishedAssignment(Base):
    __tablename__ = "published_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_key = Column(Text, unique=True, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    question_seed_id = Column(Integer, ForeignKey("question_seeds.id"), nullable=False)
    status = Column(Text, nullable=False, default="published")
    target_mode = Column(Text, nullable=False, default="all")
    target_student_codes = Column(Text, nullable=False, default="[]")
    due_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="published_assignments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    action = Column(Text, nullable=False)
    resource_type = Column(Text, nullable=False)
    resource_id = Column(Text, nullable=True)
    details = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class TeacherReport(Base):
    __tablename__ = "teacher_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    question_seed_id = Column(Integer, ForeignKey("question_seeds.id"), nullable=True)
    weakest_concepts = Column(Text, default="[]")
    common_misconceptions = Column(Text, default="[]")
    recommended_focus = Column(Text, default="[]")
    suggested_activity = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
