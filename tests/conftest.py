"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.base import Base


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_csv_file(fixtures_dir):
    """Return path to valid_complete.csv test file."""
    return fixtures_dir / "valid_complete.csv"


@pytest.fixture
def test_csv_partial(fixtures_dir):
    """Return path to valid_partial.csv test file."""
    return fixtures_dir / "valid_partial.csv"


@pytest.fixture
def test_csv_duplicates(fixtures_dir):
    """Return path to valid_with_duplicates.csv test file."""
    return fixtures_dir / "valid_with_duplicates.csv"


@pytest.fixture
def test_csv_bad_dates(fixtures_dir):
    """Return path to invalid_bad_dates.csv test file."""
    return fixtures_dir / "invalid_bad_dates.csv"


@pytest.fixture
def test_csv_negative_nav(fixtures_dir):
    """Return path to invalid_negative_nav.csv test file."""
    return fixtures_dir / "invalid_negative_nav.csv"


@pytest.fixture
def test_csv_missing_fields(fixtures_dir):
    """Return path to invalid_missing_fields.csv test file."""
    return fixtures_dir / "invalid_missing_fields.csv"


@pytest.fixture
def test_csv_empty(fixtures_dir):
    """Return path to empty.csv test file."""
    return fixtures_dir / "empty.csv"


@pytest.fixture
def test_csv_utf8(fixtures_dir):
    """Return path to utf8_encoding.csv test file."""
    return fixtures_dir / "utf8_encoding.csv"


@pytest.fixture
def test_csv_latin1(fixtures_dir):
    """Return path to latin1_encoding.csv test file."""
    return fixtures_dir / "latin1_encoding.csv"


@pytest.fixture(scope="session")
def test_database_url():
    """Return test database URL."""
    # Use SQLite in-memory database for tests (or PostgreSQL test database)
    return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def test_db_engine(test_database_url):
    """Create test database engine."""
    if "sqlite" in test_database_url:
        # SQLite in-memory configuration
        engine = create_engine(
            test_database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # PostgreSQL configuration
        engine = create_engine(test_database_url, echo=False)

    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create test database session."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_session(test_db_session):
    """Alias for test_db_session for convenience."""
    return test_db_session


@pytest.fixture
def db(test_db_engine, test_db_session):
    """Create test database with tables initialized."""
    # Create all tables
    Base.metadata.create_all(bind=test_db_engine)
    
    yield test_db_session
    
    # Cleanup is handled by test_db_session fixture


# Pytest hooks

def pytest_configure(config):
    """Configure pytest."""
    # Add markers to registry
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow")
