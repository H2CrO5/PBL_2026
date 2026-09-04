"""Database engine and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL, DB_PATH
from db.models import Base

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables():
    """Create all ORM tables."""
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)

    def add_columns(table: str, definitions: dict[str, str]):
        if table not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns(table)}
        with engine.begin() as connection:
            for name, definition in definitions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))

    add_columns("courses", {"external_key": "TEXT"})
    add_columns("materials", {
        "external_key": "TEXT",
        "audience": "TEXT NOT NULL DEFAULT 'student'",
    })
    add_columns("question_seeds", {
        "points": "FLOAT NOT NULL DEFAULT 100",
        "max_attempts": "INTEGER NOT NULL DEFAULT 1",
    })
    add_columns("teacher_reports", {
        "opening_activity": "TEXT",
        "review_sequence": "TEXT NOT NULL DEFAULT '[]'",
        "in_class_check": "TEXT",
        "follow_up_actions": "TEXT NOT NULL DEFAULT '[]'",
        "recommended_seed_titles": "TEXT NOT NULL DEFAULT '[]'",
    })
    with engine.begin() as connection:
        # Historical demo rows used "ready" before shared RAG existed. Mark
        # them explicitly as waiting for sync instead of implying indexing.
        connection.execute(text(
            "UPDATE materials SET ingestion_status = 'local_only' "
            "WHERE ingestion_status = 'ready'"
        ))
        connection.execute(text(
            "UPDATE question_seeds SET difficulty = CASE difficulty "
            "WHEN 'supportive' THEN 'easy' WHEN 'balanced' THEN 'medium' "
            "WHEN 'challenging' THEN 'hard' ELSE difficulty END"
        ))
        connection.execute(text(
            "UPDATE courses SET external_key = 'course-' || id WHERE external_key IS NULL"
        ))
        connection.execute(text(
            "UPDATE materials SET external_key = 'material-' || id WHERE external_key IS NULL"
        ))
        # Older versions treated every RAG material as student-visible. Keep
        # normal lecture files public, but classify clearly labeled teacher
        # notes as internal and stop advertising them as indexed for Student.
        connection.execute(text(
            "UPDATE materials SET audience = 'teacher', ingestion_status = 'teacher_only' "
            "WHERE lower(title) LIKE 'teacher note:%' "
            "OR lower(title) LIKE 'teacher prompt:%' "
            "OR title LIKE '教員メモ:%' OR title LIKE '教員メモ：%' "
            "OR title LIKE '教員向けメモ:%' OR title LIKE '教員向けメモ：%'"
        ))
        # Keep existing local demo databases aligned with the current UI seed.
        connection.execute(text(
            "UPDATE teachers SET name = '東北一郎' "
            "WHERE teacher_code = 't2024001' AND name = 'Professor Demo'"
        ))


def get_db():
    """Yield a database session for FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
