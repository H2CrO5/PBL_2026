"""SQLAlchemy ORM models for the student education system."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    overall_score = Column(Float, default=0.0)
    total_answered = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    weak_topics = Column(Text, default="[]")
    strong_topics = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")
    chat_messages = relationship("ChatMessage", back_populates="student")
    sessions = relationship("Session", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_key = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    term = Column(Text, nullable=False, default="unspecified")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    enrollments = relationship("Enrollment", back_populates="course")
    lectures = relationship("Lecture", back_populates="course")
    materials = relationship("CourseMaterial", back_populates="course")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("course_id", "student_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(Text, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    external_key = Column(Text, nullable=True)
    lecture_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    lecture_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="lecture")
    course = relationship("Course", back_populates="lectures")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    external_key = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=True)
    topic = Column(Text, nullable=False)
    difficulty = Column(Text, nullable=False)  # easy / medium / hard
    question_text = Column(Text, nullable=False)
    choices = Column(Text, nullable=True)  # JSON for multiple choice
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    rubric = Column(Text, nullable=False, default="[]")
    points = Column(Float, nullable=False, default=100.0)
    max_attempts = Column(Integer, nullable=False, default=1)
    due_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    question_type = Column(Text, nullable=False)  # multiple_choice / short_answer / code
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="assignments")
    lecture = relationship("Lecture", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=False)
    source = Column(Text, nullable=False, default="real")  # real / seed / synthetic
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(Text, nullable=False, default="graded")
    max_score = Column(Float, nullable=False, default=100.0)
    auto_score = Column(Float, nullable=True)
    auto_feedback = Column(Text, nullable=True)
    missing_concepts = Column(Text, nullable=False, default="[]")
    teacher_error_pattern = Column(Text, nullable=True)
    grading_source = Column(Text, nullable=False, default="auto")
    reviewed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    role = Column(Text, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="chat_messages")


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_key = Column(Text, unique=True, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=True)
    title = Column(Text, nullable=False)
    material_type = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    ingestion_status = Column(Text, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="materials")
    chunks = relationship("MaterialChunk", back_populates="material", cascade="all, delete-orphan")


class MaterialChunk(Base):
    __tablename__ = "material_chunks"
    __table_args__ = (UniqueConstraint("material_id", "chunk_index"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("course_materials.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON vector; null means lexical fallback
    source_locator = Column(Text, nullable=True)

    material = relationship("CourseMaterial", back_populates="chunks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_type = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    resource_type = Column(Text, nullable=False)
    resource_id = Column(Text, nullable=True)
    details = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    token = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    student = relationship("Student", back_populates="sessions")
