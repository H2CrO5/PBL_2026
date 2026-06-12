"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL, DB_PATH
from db.models import Base

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables():
    """Create all tables defined in the ORM models."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a database session (for FastAPI dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
