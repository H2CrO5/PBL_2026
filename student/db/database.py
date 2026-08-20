"""Database engine and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL, DB_PATH
from db.models import Base

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables():
    """Create all tables defined in the ORM models."""
    Base.metadata.create_all(bind=engine)
    # create_all does not add columns to an existing SQLite database. Keep the
    # prototype database forward-compatible without requiring Alembic yet.
    inspector = inspect(engine)

    def add_columns(table: str, definitions: dict[str, str]):
        if table not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns(table)}
        with engine.begin() as connection:
            for name, definition in definitions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))

    add_columns("lectures", {
        "course_id": "INTEGER",
        "external_key": "TEXT",
    })
    add_columns("assignments", {
        "course_id": "INTEGER",
        "external_key": "TEXT",
        "title": "TEXT",
        "rubric": "TEXT NOT NULL DEFAULT '[]'",
        "points": "FLOAT NOT NULL DEFAULT 100",
        "max_attempts": "INTEGER NOT NULL DEFAULT 1",
        "due_at": "DATETIME",
        "published_at": "DATETIME",
    })
    add_columns("submissions", {
        "source": "TEXT NOT NULL DEFAULT 'seed'",
        "attempt_number": "INTEGER NOT NULL DEFAULT 1",
        "status": "TEXT NOT NULL DEFAULT 'graded'",
        "max_score": "FLOAT NOT NULL DEFAULT 100",
        "auto_score": "FLOAT",
        "auto_feedback": "TEXT",
        "missing_concepts": "TEXT NOT NULL DEFAULT '[]'",
        "teacher_error_pattern": "TEXT",
        "grading_source": "TEXT NOT NULL DEFAULT 'auto'",
        "reviewed_at": "DATETIME",
    })

    # Preserve legacy records by placing them in one explicit course. New
    # Teacher-published content uses stable external keys instead of local IDs.
    with engine.begin() as connection:
        legacy = connection.execute(
            text("SELECT id FROM courses WHERE external_key = 'legacy-course'")
        ).first()
        if legacy is None:
            connection.execute(text(
                "INSERT INTO courses (external_key, title, term, created_at, updated_at) "
                "VALUES ('legacy-course', 'Legacy Student Course', 'unspecified', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ))
            legacy = connection.execute(
                text("SELECT id FROM courses WHERE external_key = 'legacy-course'")
            ).first()
        legacy_id = legacy[0]
        connection.execute(text("UPDATE lectures SET course_id = :course_id WHERE course_id IS NULL"), {"course_id": legacy_id})
        connection.execute(text("UPDATE assignments SET course_id = :course_id WHERE course_id IS NULL"), {"course_id": legacy_id})
        connection.execute(text(
            "INSERT OR IGNORE INTO enrollments (course_id, student_id, status, created_at) "
            "SELECT :course_id, id, 'active', CURRENT_TIMESTAMP FROM students"
        ), {"course_id": legacy_id})


def get_db():
    """Yield a database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
