"""Database configuration and session management."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Read database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fundlens.db")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI endpoints.

    Yields a database session and ensures cleanup.

    Usage in FastAPI:
        @app.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
