"""Database engine and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATABASE_URL,
    DB_PATH,
    DEFAULT_COURSE_EXTERNAL_KEY,
    DEFAULT_COURSE_TERM,
    DEFAULT_COURSE_TITLE,
)
from db.models import Base

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _student_safe_content(content: str) -> str:
    """Remove explicitly labeled teacher-only sections from public content."""
    public_lines = []
    skipping_internal = False
    internal_prefixes = (
        "teacher note:",
        "teacher note：",
        "teacher prompt:",
        "teacher prompt：",
        "教員メモ:",
        "教員メモ：",
        "教員向けメモ:",
        "教員向けメモ：",
    )
    for line in content.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if any(lowered.startswith(prefix) for prefix in internal_prefixes):
            skipping_internal = True
            continue
        if skipping_internal and (
            stripped.startswith("#")
            or stripped.lower().startswith("[slide ")
            or stripped.lower().startswith("[page ")
        ):
            skipping_internal = False
        if not skipping_internal:
            public_lines.append(line)
    return "\n".join(public_lines).strip()


def _lexical_chunks(content: str) -> list[str]:
    chunks = []
    start = 0
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    while start < len(content):
        chunk = content[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def _ensure_default_course(connection) -> int:
    """Create or migrate the shared default course without losing Student data."""
    canonical = connection.execute(
        text("SELECT id FROM courses WHERE external_key = :external_key"),
        {"external_key": DEFAULT_COURSE_EXTERNAL_KEY},
    ).first()
    legacy = connection.execute(
        text("SELECT id FROM courses WHERE external_key = 'legacy-course'")
    ).first()

    if canonical is None and legacy is not None:
        # The deployed prototype normally follows this path. Renaming the row
        # keeps every existing lecture, assignment, submission, and enrollment
        # attached through its unchanged primary key.
        connection.execute(text(
            "UPDATE courses SET external_key = :external_key, title = :title, "
            "term = :term, updated_at = CURRENT_TIMESTAMP WHERE id = :course_id"
        ), {
            "external_key": DEFAULT_COURSE_EXTERNAL_KEY,
            "title": DEFAULT_COURSE_TITLE,
            "term": DEFAULT_COURSE_TERM,
            "course_id": legacy[0],
        })
        canonical_id = legacy[0]
        legacy = None
    else:
        if canonical is None:
            connection.execute(text(
                "INSERT INTO courses (external_key, title, term, created_at, updated_at) "
                "VALUES (:external_key, :title, :term, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ), {
                "external_key": DEFAULT_COURSE_EXTERNAL_KEY,
                "title": DEFAULT_COURSE_TITLE,
                "term": DEFAULT_COURSE_TERM,
            })
            canonical = connection.execute(
                text("SELECT id FROM courses WHERE external_key = :external_key"),
                {"external_key": DEFAULT_COURSE_EXTERNAL_KEY},
            ).first()
        canonical_id = canonical[0]

    if legacy is not None and legacy[0] != canonical_id:
        legacy_id = legacy[0]
        # If both rows already exist, merge the legacy relationships into the
        # shared course. INSERT OR IGNORE avoids duplicate enrollments.
        connection.execute(text(
            "INSERT OR IGNORE INTO enrollments (course_id, student_id, status, created_at) "
            "SELECT :canonical_id, student_id, status, created_at FROM enrollments "
            "WHERE course_id = :legacy_id"
        ), {"canonical_id": canonical_id, "legacy_id": legacy_id})
        for table in ("lectures", "assignments", "course_materials", "chat_messages"):
            connection.execute(
                text(f"UPDATE {table} SET course_id = :canonical_id WHERE course_id = :legacy_id"),
                {"canonical_id": canonical_id, "legacy_id": legacy_id},
            )
        connection.execute(
            text("DELETE FROM enrollments WHERE course_id = :legacy_id"),
            {"legacy_id": legacy_id},
        )
        connection.execute(
            text("DELETE FROM courses WHERE id = :legacy_id"),
            {"legacy_id": legacy_id},
        )

    connection.execute(
        text("UPDATE lectures SET course_id = :course_id WHERE course_id IS NULL"),
        {"course_id": canonical_id},
    )
    connection.execute(
        text("UPDATE assignments SET course_id = :course_id WHERE course_id IS NULL"),
        {"course_id": canonical_id},
    )
    connection.execute(
        text("UPDATE chat_messages SET course_id = :course_id WHERE course_id IS NULL"),
        {"course_id": canonical_id},
    )
    connection.execute(text(
        "INSERT OR IGNORE INTO enrollments (course_id, student_id, status, created_at) "
        "SELECT :course_id, id, 'active', CURRENT_TIMESTAMP FROM students"
    ), {"course_id": canonical_id})
    return canonical_id


def create_tables():
    """Create all tables defined in the ORM models."""
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "sqlite":
        # Production databases are created from the current metadata. The
        # ALTER/legacy-copy steps below exist only for local prototype SQLite.
        return
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
    add_columns("chat_messages", {
        "course_id": "INTEGER",
        "assignment_id": "INTEGER",
    })
    add_columns("course_materials", {
        "audience": "TEXT NOT NULL DEFAULT 'student'",
    })

    # Preserve prototype records while moving them to the course identity used
    # by Teacher. This is idempotent and retains existing submissions.
    with engine.begin() as connection:
        _ensure_default_course(connection)
        # Remove previously leaked teacher-note records and their RAG chunks.
        private_ids = [
            row[0]
            for row in connection.execute(text(
                "SELECT id FROM course_materials "
                "WHERE audience = 'teacher' "
                "OR lower(title) LIKE 'teacher note:%' "
                "OR lower(title) LIKE 'teacher prompt:%' "
                "OR title LIKE '教員メモ:%' OR title LIKE '教員メモ：%' "
                "OR title LIKE '教員向けメモ:%' OR title LIKE '教員向けメモ：%'"
            )).all()
        ]
        for material_id in private_ids:
            connection.execute(
                text("DELETE FROM material_chunks WHERE material_id = :material_id"),
                {"material_id": material_id},
            )
            connection.execute(
                text("DELETE FROM course_materials WHERE id = :material_id"),
                {"material_id": material_id},
            )

        # Older public materials may contain labeled Teacher note/prompt
        # sections inside otherwise student-facing documents. Sanitize both
        # the material body and its lexical index during migration.
        rows = connection.execute(text(
            "SELECT id, content FROM course_materials WHERE audience = 'student'"
        )).all()
        for material_id, content in rows:
            safe_content = _student_safe_content(content)
            if safe_content == content:
                continue
            connection.execute(
                text("DELETE FROM material_chunks WHERE material_id = :material_id"),
                {"material_id": material_id},
            )
            if not safe_content:
                connection.execute(
                    text("DELETE FROM course_materials WHERE id = :material_id"),
                    {"material_id": material_id},
                )
                continue
            connection.execute(text(
                "UPDATE course_materials SET content = :content, "
                "ingestion_status = 'ready_lexical', updated_at = CURRENT_TIMESTAMP "
                "WHERE id = :material_id"
            ), {"content": safe_content, "material_id": material_id})
            for index, chunk in enumerate(_lexical_chunks(safe_content)):
                connection.execute(text(
                    "INSERT INTO material_chunks "
                    "(material_id, chunk_index, text, embedding, source_locator) "
                    "VALUES (:material_id, :chunk_index, :text, NULL, :source_locator)"
                ), {
                    "material_id": material_id,
                    "chunk_index": index,
                    "text": chunk,
                    "source_locator": f"chunk-{index + 1}",
                })


def get_db():
    """Yield a database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
