"""File upload endpoint for fund data ingestion."""

import logging
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, Depends, status
from sqlalchemy.orm import Session

from src.config import Config
from src.database.db import get_db
from src.database.models import UploadJob
from src.schemas.ingestion import UploadJobResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


def validate_file_upload(file: UploadFile) -> tuple[str, int]:
    """
    Validate uploaded file type and size.

    Args:
        file: UploadFile from FastAPI

    Returns:
        Tuple of (file_extension, file_size) if valid

    Raises:
        HTTPException with appropriate status code if invalid
    """
    # Get file extension
    file_name = file.filename or ""
    file_ext = Path(file_name).suffix.lower()

    # Check extension
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        logger.warning(
            f"Invalid file type attempted: {file_ext}. Allowed: {Config.ALLOWED_EXTENSIONS}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file_ext}'. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}",
        )

    # Check file size (we'll check actual size after reading)
    # For now, we'll validate during save
    return file_ext, 0


def save_uploaded_file(file: UploadFile, job_id: str, file_ext: str) -> Path:
    """
    Save uploaded file to staging directory.

    Args:
        file: UploadFile from FastAPI
        job_id: Unique job identifier
        file_ext: File extension

    Returns:
        Path to saved file

    Raises:
        HTTPException if file save fails or size exceeds limit
    """
    try:
        # Create job staging directory
        job_staging_dir = Path(Config.STAGING_DIR) / job_id
        job_staging_dir.mkdir(parents=True, exist_ok=True)

        # Construct file path
        file_path = job_staging_dir / f"upload{file_ext}"

        # Read and save file with size check
        file_size = 0
        max_size = Config.get_file_size_limit()

        with open(file_path, "wb") as f:
            for chunk in iter(lambda: file.file.read(8192), b""):
                file_size += len(chunk)
                if file_size > max_size:
                    # Clean up partial file
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum of {Config.MAX_FILE_SIZE_MB}MB",
                    )
                f.write(chunk)

        logger.info(f"File saved successfully: {file_path} (size: {file_size} bytes)")
        return file_path

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}", exc_info=True)
        # Cleanup directory on failure
        try:
            job_staging_dir = Path(Config.STAGING_DIR) / job_id
            if job_staging_dir.exists():
                shutil.rmtree(job_staging_dir)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up staging directory: {str(cleanup_error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        )


def create_upload_job_record(
    file_name: str, job_id: str, db: Session
) -> UploadJob:
    """
    Create UploadJob record in database.

    Args:
        file_name: Original file name
        job_id: Unique job identifier
        db: Database session

    Returns:
        Created UploadJob object

    Raises:
        HTTPException if database operation fails
    """
    try:
        upload_job = UploadJob(
            status="processing",
            file_name=file_name,
            imported_count=0,
            rejected_count=0,
        )
        db.add(upload_job)
        db.commit()
        db.refresh(upload_job)
        logger.info(f"UploadJob created: id={upload_job.id}, job_id={job_id}, file={file_name}")
        return upload_job
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating UploadJob record: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create upload job record",
        )


async def process_upload_async(job_id: str, upload_job_id: int) -> None:
    """
    Async background task to process uploaded file.

    Args:
        job_id: Unique job identifier
        upload_job_id: Database UploadJob ID

    This is a placeholder that will be implemented in Task 6.1.
    For now, it just logs that processing would begin.
    """
    logger.info(f"Background task started for job_id={job_id}, upload_job_id={upload_job_id}")
    # Placeholder - actual processing will be implemented in Task 6.1
    logger.info(f"Processing would begin here for {job_id}")


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, response_model=UploadJobResponse)
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> UploadJobResponse:
    """
    Upload a CSV or Excel file for fund data ingestion.

    Accepts multipart file upload, validates it, stores it in staging,
    creates a database record, and queues an async processing task.

    Args:
        file: Uploaded file (CSV or Excel)
        background_tasks: FastAPI background tasks manager
        db: Database session

    Returns:
        UploadJobResponse with job status and ID

    Raises:
        HTTPException with appropriate status codes:
        - 400: Invalid file type
        - 413: File too large
        - 500: Server error during upload processing
    """
    # Generate unique job ID
    job_id = str(uuid4())
    logger.info(f"Upload initiated: job_id={job_id}, file={file.filename}")

    try:
        # Validate file
        file_ext, _ = validate_file_upload(file)

        # Save file to staging
        file_path = save_uploaded_file(file, job_id, file_ext)

        # Create UploadJob record
        upload_job = create_upload_job_record(file.filename or "unknown", job_id, db)

        # Queue async processing task
        background_tasks.add_task(
            process_upload_async, job_id, upload_job.id
        )
        logger.info(f"Background task queued for job_id={job_id}")

        # Return immediate response with job ID
        return UploadJobResponse(
            id=upload_job.id,
            status="processing",
            file_name=upload_job.file_name,
            imported_count=0,
            rejected_count=0,
            errors=[],
            created_at=upload_job.created_at.isoformat(),
            completed_at=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during file upload",
        )
