"""Integration tests for file upload endpoint."""

import json
from pathlib import Path
from io import BytesIO
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from src.database.models import UploadJob
from src.database.base import Base
from src.database.db import get_db
from src.config import Config
from src.api import upload


@asynccontextmanager
async def test_lifespan(app: FastAPI):
    """Test lifespan that skips database creation (handled by fixture)."""
    # Startup - skip DB creation as it's handled by fixtures
    yield
    # Shutdown - do nothing


@pytest.fixture
def client():
    """FastAPI test client with fresh test database for each test."""
    # Create fresh in-memory database for this test
    test_database_url = f"sqlite:///:memory:?cache=shared&{uuid4()}"
    test_db_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create test database session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_db_engine)
    
    # Create a test app with test lifespan
    test_app = FastAPI(
        title="FundLens Data Ingestion API (Test)",
        description="API for uploading and processing fund data",
        version="1.0.0",
        lifespan=test_lifespan,
    )
    
    # Register routers
    test_app.include_router(upload.router)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the dependency
    test_app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(test_app)
    
    yield client
    
    # Cleanup
    Base.metadata.drop_all(bind=test_db_engine)
    test_app.dependency_overrides.clear()
    test_db_engine.dispose()


@pytest.fixture
def sample_csv():
    """Create a sample CSV file for testing."""
    csv_content = b"""Fund Name,Date,NAV,Category
Vanguard 500,2024-01-15,150.25,Equity
Fidelity Growth,2024-01-15,200.50,Equity
HDFC Hybrid,2024-01-15,50.00,Hybrid"""
    return BytesIO(csv_content)


@pytest.fixture
def sample_excel():
    """Create a sample Excel file for testing."""
    try:
        import openpyxl
        from openpyxl.utils.dataframe import dataframe_to_rows
        import pandas as pd

        # Create a simple Excel file
        df = pd.DataFrame({
            "Fund Name": ["Vanguard 500", "Fidelity Growth", "HDFC Hybrid"],
            "Date": ["2024-01-15", "2024-01-15", "2024-01-15"],
            "NAV": [150.25, 200.50, 50.00],
            "Category": ["Equity", "Equity", "Hybrid"],
        })

        # Write to bytes
        excel_bytes = BytesIO()
        with pd.ExcelWriter(excel_bytes, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        excel_bytes.seek(0)
        return excel_bytes
    except ImportError:
        pytest.skip("openpyxl not installed")


@pytest.fixture
def invalid_file():
    """Create an invalid file (JSON) for testing."""
    json_content = b"""{"fund": "test"}"""
    return BytesIO(json_content)


class TestUploadEndpoint:
    """Tests for the /api/upload endpoint."""

    def test_upload_csv_success(self, client, sample_csv):
        """Test successful CSV upload."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", sample_csv, "text/csv")},
        )

        assert response.status_code == 202
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["status"] == "processing"
        assert data["file_name"] == "test.csv"
        assert data["imported_count"] == 0
        assert data["rejected_count"] == 0
        assert data["errors"] == []
        assert "created_at" in data
        assert data["completed_at"] is None

    def test_upload_excel_success(self, client, sample_excel):
        """Test successful Excel upload."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", sample_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

        assert response.status_code == 202
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["status"] == "processing"
        assert data["file_name"] == "test.xlsx"
        assert data["imported_count"] == 0
        assert data["rejected_count"] == 0

    def test_upload_invalid_file_type(self, client, invalid_file):
        """Test upload with invalid file type."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.json", invalid_file, "application/json")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid file type" in data["detail"]

    def test_upload_missing_file(self, client):
        """Test upload without file."""
        response = client.post("/api/upload")

        assert response.status_code == 422  # Unprocessable entity

    def test_upload_file_too_large(self, client):
        """Test upload with file exceeding size limit."""
        # Create a file larger than the limit
        large_content = b"x" * (Config.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
        large_file = BytesIO(large_content)

        response = client.post(
            "/api/upload",
            files={"file": ("large.csv", large_file, "text/csv")},
        )

        assert response.status_code == 413
        data = response.json()
        assert "detail" in data
        assert "exceeds maximum" in data["detail"]

    def test_upload_creates_staging_directory(self, client, sample_csv, tmp_path):
        """Test that upload creates staging directory."""
        # Note: This test verifies file is saved but uses actual staging dir
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", sample_csv, "text/csv")},
        )

        assert response.status_code == 202
        data = response.json()

        # Verify staging directory was created
        staging_dir = Path(Config.STAGING_DIR)
        assert staging_dir.exists()

    def test_upload_creates_database_record(self, client, test_db_engine):
        """Test that upload creates UploadJob record in database."""
        from sqlalchemy.orm import sessionmaker
        TestingSessionLocal = sessionmaker(bind=test_db_engine)
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", BytesIO(b"Fund Name,Date,NAV,Category\nVanguard 500,2024-01-15,150.25,Equity"), "text/csv")},
        )

        assert response.status_code == 202
        data = response.json()

        # Query database for the job
        db = TestingSessionLocal()
        try:
            upload_job = db.query(UploadJob).filter_by(id=data["id"]).first()
            assert upload_job is not None
            assert upload_job.status == "processing"
            assert upload_job.file_name == "test.csv"
            assert upload_job.imported_count == 0
            assert upload_job.rejected_count == 0
        finally:
            db.close()

    def test_upload_response_has_job_id(self, client, sample_csv):
        """Test that upload response includes job ID for polling."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", sample_csv, "text/csv")},
        )

        assert response.status_code == 202
        data = response.json()

        # Job ID should be present and not None
        assert data["id"] is not None
        assert isinstance(data["id"], int)

    def test_upload_multiple_files_different_job_ids(self, client, sample_csv):
        """Test that multiple uploads get different job IDs."""
        response1 = client.post(
            "/api/upload",
            files={"file": ("test1.csv", BytesIO(sample_csv.getvalue()), "text/csv")},
        )
        response2 = client.post(
            "/api/upload",
            files={"file": ("test2.csv", BytesIO(sample_csv.getvalue()), "text/csv")},
        )

        assert response1.status_code == 202
        assert response2.status_code == 202

        data1 = response1.json()
        data2 = response2.json()

        # Job IDs should be different
        assert data1["id"] != data2["id"]


class TestUploadValidation:
    """Tests for upload file validation."""

    def test_csv_extension_accepted(self, client, sample_csv):
        """Test that .csv extension is accepted."""
        response = client.post(
            "/api/upload",
            files={"file": ("data.csv", sample_csv, "text/csv")},
        )
        assert response.status_code == 202

    def test_xlsx_extension_accepted(self, client, sample_excel):
        """Test that .xlsx extension is accepted."""
        response = client.post(
            "/api/upload",
            files={"file": ("data.xlsx", sample_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 202

    def test_txt_extension_rejected(self, client):
        """Test that .txt extension is rejected."""
        text_file = BytesIO(b"some text")
        response = client.post(
            "/api/upload",
            files={"file": ("data.txt", text_file, "text/plain")},
        )
        assert response.status_code == 400

    def test_json_extension_rejected(self, client, invalid_file):
        """Test that .json extension is rejected."""
        response = client.post(
            "/api/upload",
            files={"file": ("data.json", invalid_file, "application/json")},
        )
        assert response.status_code == 400
