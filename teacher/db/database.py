"""Database engine and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL, DB_PATH
from db.models import Base

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables():
    """Create all ORM tables."""
    Base.metadata.create_all(bind=engine)
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
    add_columns("materials", {"external_key": "TEXT"})
    add_columns("question_seeds", {
        "points": "FLOAT NOT NULL DEFAULT 100",
        "max_attempts": "INTEGER NOT NULL DEFAULT 1",
    })
    with engine.begin() as connection:
        connection.execute(text(
            "UPDATE courses SET external_key = 'course-' || id WHERE external_key IS NULL"
        ))
        connection.execute(text(
            "UPDATE materials SET external_key = 'material-' || id WHERE external_key IS NULL"
        ))


def get_db():
    """Yield a database session for FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
