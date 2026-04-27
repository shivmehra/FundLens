# Phase 1: Data Ingestion Pipeline — Detailed Implementation Plan

## Overview

Build a robust, production-ready data ingestion system that accepts CSV and Excel files, validates fund data against a flexible schema, detects duplicates, and imports normalized data into PostgreSQL with comprehensive error reporting and user feedback.

**What we're delivering:** Complete data pipeline from file upload through PostgreSQL persistence, with partial-acceptance validation, async job processing, and status polling.

---

## Task Breakdown

### Group 1: Project Setup & Infrastructure (Wave 1)

These tasks establish the foundation for all subsequent work and can run in parallel.

#### Task 1.1: Project Structure & Dependencies

**Effort:** Small | **Depends on:** None

**Description:**

- Create project directories: `src/`, `src/ingestion/`, `src/models/`, `src/api/`, `src/parsers/`, `src/validators/`, `src/database/`, `tests/`, `tests/fixtures/`
- Initialize `requirements.txt` with core dependencies:
  - **FastAPI** (async HTTP framework)
  - **Pandas** (CSV/Excel parsing)
  - **openpyxl** (Excel support)
  - **Pydantic v2** (schema validation)
  - **SQLAlchemy** (ORM)
  - **psycopg2-binary** or **asyncpg** (PostgreSQL client)
  - **Alembic** (database migrations)
  - **python-multipart** (file upload handling)
  - **pytest** (testing)
  - **pytest-asyncio** (async test support)
- Create `.env.example` with required environment variables:
  - `DATABASE_URL=postgresql://user:pass@localhost/fundlens`
  - `STAGING_DIR=./uploads/staging`
  - `STAGING_TTL_DAYS=7`
  - `LOG_LEVEL=INFO`

**Acceptance Criteria:**

- ✓ All directories created with `__init__.py` files
- ✓ `requirements.txt` has all dependencies with pinned versions
- ✓ `.env.example` covers all configurable parameters
- ✓ `pip install -r requirements.txt` succeeds without errors

---

#### Task 1.2: PostgreSQL & Alembic Setup

**Effort:** Small | **Depends on:** Task 1.1

**Description:**

- Create PostgreSQL database: `fundlens` (or use existing local instance)
- Initialize Alembic in `db/migrations/` directory
- Create Alembic environment configuration with SQLAlchemy URL from `DATABASE_URL` env var
- Verify Alembic can connect to database and generate migration templates
- Document migration workflow in `docs/database.md`

**Acceptance Criteria:**

- ✓ `fundlens` database exists and is empty
- ✓ Alembic initialized: `alembic/` directory structure present
- ✓ `alembic revision --autogenerate` command works
- ✓ Test connection: `alembic stamp head` succeeds (or stamp to appropriate version)

---

#### Task 1.3: Data Models & Pydantic Schemas

**Effort:** Medium | **Depends on:** Task 1.1

**Description:**

- Create `src/models/domain.py` with core domain models:
  - **Fund** (id, name, category, inception_date, created_at, updated_at)
  - **NavHistory** (id, fund_id, date, nav, created_at)
  - **FundMetadata** (id, fund_id, manager, allocation, sharpe_ratio, max_drawdown, cagr, aum)
  - **UploadJob** (id, status, file_name, imported_count, rejected_count, errors, created_at)
- Create `src/schemas/ingestion.py` with Pydantic schemas:
  - **FundDataRow** (pydantic BaseModel with validators for fund_name, date, nav, category)
  - **UploadJobResponse** (for status endpoint returns)
  - **ErrorDetail** (row_number, field, error_message, value)
- Implement flexible schema configuration in `src/config/schema.py`:
  - Define required fields (fund_name, date, nav, category)
  - Define optional fields with defaults (inception_date, manager, etc.)
  - Field mapping configuration (e.g., CSV "Fund Name" → "fund_name")
  - Load schema config from JSON file: `config/schema.json`
- Add custom validators to Pydantic schemas:
  - Date format: ISO-8601 YYYY-MM-DD
  - NAV: positive decimal
  - Fund name: non-empty string
  - Category: validated against allowed categories ("Equity", "Debt", "Hybrid", etc.)

**Acceptance Criteria:**

- ✓ All domain models defined in `src/models/domain.py`
- ✓ All Pydantic schemas in `src/schemas/ingestion.py` with validators
- ✓ Schema config loaded from `config/schema.json` and can be modified at runtime
- ✓ Validators catch invalid data (bad dates, negative NAV, empty names)
- ✓ Unit tests for schema validation pass

---

#### Task 1.4: Database Models & Initial Migration

**Effort:** Medium | **Depends on:** Task 1.2, Task 1.3

**Description:**

- Create SQLAlchemy ORM models in `src/database/models.py`:
  - **Fund** table: id (PK), name (VARCHAR), category (VARCHAR), inception_date (DATE, nullable), created_at, updated_at
  - **NavHistory** table: id (PK), fund_id (FK), date (DATE), nav (NUMERIC), created_at
  - **FundMetadata** table: id (PK), fund_id (FK), manager, allocation, sharpe_ratio, etc. (all nullable)
  - **UploadJob** table: id (PK), status, file_name, imported_count, rejected_count, error_json, created_at
- Add database constraints:
  - UNIQUE constraint: `nav_history(fund_id, date)` — prevent duplicate nav entries
  - UNIQUE constraint: `funds(name)` — fund names are unique
  - Foreign keys: `nav_history.fund_id → funds.id`, `fund_metadata.fund_id → funds.id`, etc.
  - Indexes on: `funds.name`, `nav_history.date`, `nav_history.fund_id`
- Create initial Alembic migration:
  - `alembic revision --autogenerate -m "Initial schema: funds, nav_history, fund_metadata"`
  - Verify migration SQL is correct before applying
  - `alembic upgrade head` applies migration

**Acceptance Criteria:**

- ✓ All ORM models defined with correct types and relationships
- ✓ Constraints and indexes created in migration
- ✓ `alembic upgrade head` creates tables in PostgreSQL
- ✓ `\dt` in psql shows: funds, nav_history, fund_metadata, upload_jobs tables
- ✓ Foreign key constraints enforced

---

#### Task 1.5: Test Infrastructure & Fixtures

**Effort:** Medium | **Depends on:** Task 1.1, Task 1.2

**Description:**

- Create `tests/conftest.py` with pytest fixtures:
  - **test_db** fixture: creates temporary PostgreSQL schema for each test, tears down after
  - **app** fixture: FastAPI test client configured with test database
  - **db_session** fixture: SQLAlchemy session for test database
- Create test fixture files in `tests/fixtures/`:
  - **valid_complete.csv**: 10 rows with all required fields + optional fields, valid data, no duplicates
  - **valid_partial.csv**: 10 rows with required fields, optional fields missing (null), valid data
  - **valid_with_duplicates.csv**: 10 rows including 2 duplicate (fund_name, date) pairs for duplicate detection testing
  - **invalid_missing_fields.csv**: 5 rows with missing required fields (no nav, no category, etc.)
  - **invalid_bad_dates.csv**: 5 rows with malformed dates (not YYYY-MM-DD)
  - **invalid_negative_nav.csv**: 5 rows with negative NAV values
  - **empty.csv**: empty file (0 rows after header)
  - **utf8_encoding.csv**: valid data in UTF-8 encoding
  - **latin1_encoding.csv**: valid data in Latin-1 encoding (for encoding detection testing)
- Create test database setup:
  - Alembic migrations run against test database before each test
  - Cleanup: database reset after each test
- Create pytest markers: `@pytest.mark.integration`, `@pytest.mark.unit`
- Configure `pytest.ini` with test discovery patterns

**Acceptance Criteria:**

- ✓ `pytest --collect-only` shows all fixtures and test markers
- ✓ `pytest -m unit` runs only unit tests
- ✓ `pytest -m integration` runs only integration tests
- ✓ Test database created fresh for each test run
- ✓ All fixture files exist in `tests/fixtures/` with correct data
- ✓ `pytest tests/` runs without errors (0 tests initially, will add in later tasks)

---

### Group 2: File Parsing & Data Extraction (Wave 2)

These tasks can run in parallel after Wave 1 completes. They implement the core parsing logic without validation or storage.

#### Task 2.1: CSV Parser

**Effort:** Medium | **Depends on:** Task 1.3

**Description:**

- Create `src/parsers/csv_parser.py` with `CSVParser` class
- Implement `parse(file_path: str) -> List[Dict[str, any]]` method:
  - Read CSV file with Pandas: `pd.read_csv(file_path)`
  - Handle encoding detection (UTF-8 preferred, fallback to ISO-8859-1, Latin-1)
  - Return list of dictionaries (one per row)
  - Each dict keys = CSV column headers (as-is from file)
- Implement `extract_rows_with_line_numbers() -> List[Tuple[int, Dict]]`:
  - Same as above but include 1-based row number for error reporting
- Error handling:
  - Catch file not found, encoding errors, malformed CSV
  - Raise descriptive exceptions with context
- Edge cases:
  - Empty CSV (header only, no data rows)
  - Very large CSV (>100MB) — stream processing if needed
  - CSV with quotes, commas in data, multiline fields
- Add logging at DEBUG level for parse operations

**Acceptance Criteria:**

- ✓ Can parse valid_complete.csv and return 10 row dicts
- ✓ Can parse valid_with_duplicates.csv
- ✓ Can detect encoding for utf8_encoding.csv and latin1_encoding.csv
- ✓ Raises descriptive error for invalid_bad_dates.csv (file structure OK, data issues deferred to validator)
- ✓ Raises descriptive error for missing files, permission errors
- ✓ Returns row numbers in extract_rows_with_line_numbers()
- ✓ Unit tests pass: `pytest -m unit tests/test_csv_parser.py`

---

#### Task 2.2: Excel Parser

**Effort:** Medium | **Depends on:** Task 1.3

**Description:**

- Create `src/parsers/excel_parser.py` with `ExcelParser` class
- Implement `parse(file_path: str, sheet_name: str = None) -> List[Dict[str, any]]`:
  - Read Excel file with Pandas: `pd.read_excel(file_path, sheet_name=sheet_name or 0)`
  - Use openpyxl as engine (via pandas)
  - Support multiple sheets: if sheet_name not provided, use first sheet
  - Return list of dictionaries (one per row)
  - Handle column headers from first row
- Implement `extract_rows_with_line_numbers() -> List[Tuple[int, Dict]]`
- Error handling:
  - Invalid .xlsx file (corrupted, wrong format)
  - Sheet not found
  - Encoding/decoding issues
  - Raise descriptive exceptions
- Edge cases:
  - Empty worksheet
  - Merged cells
  - Data types (dates might be Excel serial numbers — convert to ISO-8601 strings)
  - Missing sheet parameter (default to first sheet)

**Acceptance Criteria:**

- ✓ Can parse valid_complete.xlsx (create using pandas if not in fixtures)
- ✓ Returns data as dicts matching CSV structure
- ✓ Handles multiple sheets (default to first)
- ✓ Excel dates converted to ISO-8601 strings
- ✓ Raises descriptive errors for invalid/corrupted files
- ✓ Unit tests pass: `pytest -m unit tests/test_excel_parser.py`

---

#### Task 2.3: Unified File Parser Interface

**Effort:** Small | **Depends on:** Task 2.1, Task 2.2

**Description:**

- Create `src/parsers/__init__.py` with `parse_file(file_path: str) -> List[Tuple[int, Dict]]`:
  - Detect file type from extension (.csv, .xlsx)
  - Route to appropriate parser (CSV or Excel)
  - Return unified format: list of (row_number, row_dict) tuples
  - Raise descriptive error for unsupported file types
- Add logging for parser selection and file processing

**Acceptance Criteria:**

- ✓ `parse_file("fixture.csv")` returns list of tuples
- ✓ `parse_file("fixture.xlsx")` returns list of tuples with same structure
- ✓ Unsupported file type (.json, .txt) raises clear error
- ✓ Row numbers are 1-based in both cases
- ✓ Unit tests pass

---

### Group 3: Validation & Duplicate Detection (Wave 2)

#### Task 3.1: Data Validator

**Effort:** Medium | **Depends on:** Task 1.3, Task 2.3

**Description:**

- Create `src/validators/data_validator.py` with `DataValidator` class
- Implement `validate_row(row: Dict, row_number: int) -> Tuple[Optional[FundDataRow], Optional[ErrorDetail]]`:
  - Accept raw dict from parser + row number
  - Attempt to coerce/map CSV column names to schema fields (using field mapping from config)
  - Validate with Pydantic: `FundDataRow(**coerced_row)`
  - Return:
    - If valid: (FundDataRow object, None)
    - If invalid: (None, ErrorDetail with row_number, field, error message, original value)
- Implement field mapping logic:
  - Load mapping from `config/schema.json` (e.g., {"Fund Name": "fund_name", "NAV": "nav"})
  - Support flexible column naming
  - Raise error if required column not found in CSV
- Error messages must be user-friendly:
  - "Row 5, field 'nav': value '-100' is not a positive number"
  - "Row 8, field 'date': expected YYYY-MM-DD format, got '8/15/2024'"
- Add logging at DEBUG level

**Acceptance Criteria:**

- ✓ Can validate valid_complete.csv rows → all pass
- ✓ Can validate valid_partial.csv rows → all pass (nulls allowed for optional fields)
- ✓ Can validate invalid_negative_nav.csv rows → all fail with specific error messages
- ✓ Can validate invalid_bad_dates.csv rows → all fail with date format errors
- ✓ Field mapping works: {"Fund Name": "fund_name"} maps CSV column to schema field
- ✓ Unit tests pass: `pytest -m unit tests/test_data_validator.py`

---

#### Task 3.2: Duplicate Detector

**Effort:** Medium | **Depends on:** Task 1.3, Task 2.3

**Description:**

- Create `src/validators/duplicate_detector.py` with `DuplicateDetector` class
- Implement `detect_duplicates(rows: List[FundDataRow]) -> Dict[str, List[int]]`:
  - Group rows by (fund_name, date) key
  - Find groups with >1 row (duplicates)
  - Return dict: {key: [row_numbers]} for duplicates found
  - Example: {"Vanguard 500, 2024-01-15": [3, 7], "Fidelity Growth, 2024-02-20": [12]}
- Implement `detect_duplicates_in_database(rows: List[FundDataRow], db_session) -> Dict[str, List]`:
  - Query PostgreSQL for existing (fund_name, date) entries
  - Identify which rows would conflict with existing data
  - Return dict: {key: [row_numbers, existing_id]} for database conflicts
- User must be prompted on duplicates before storage (duplicate resolution handled in upload endpoint)

**Acceptance Criteria:**

- ✓ Can detect in-file duplicates in valid_with_duplicates.csv → returns 2 duplicate pairs
- ✓ Can detect database conflicts (after data is seeded)
- ✓ Returns user-readable key format (fund_name, date)
- ✓ Row numbers are accurate
- ✓ Unit tests pass: `pytest -m unit tests/test_duplicate_detector.py`

---

### Group 4: Database Access Layer (Wave 2)

#### Task 4.1: SQLAlchemy Session Management

**Effort:** Small | **Depends on:** Task 1.2, Task 1.4

**Description:**

- Create `src/database/db.py` with:
  - `engine` creation from DATABASE_URL env var
  - `SessionLocal` session factory
  - `get_db()` generator function (for dependency injection in FastAPI)
  - Connection pooling configuration
- Create `src/database/__init__.py` exporting `engine`, `SessionLocal`, `Base`
- Add initialization in main app: `Base.metadata.create_all(bind=engine)` (on startup)

**Acceptance Criteria:**

- ✓ `SessionLocal()` creates valid SQLAlchemy sessions
- ✓ `engine.connect()` works
- ✓ Tables exist after initialization
- ✓ No import errors

---

#### Task 4.2: Fund Repository

**Effort:** Medium | **Depends on:** Task 1.4, Task 4.1

**Description:**

- Create `src/database/repositories/fund_repo.py` with `FundRepository` class
- Implement methods:
  - `create_or_get_fund(name: str, category: str, inception_date=None, session) -> Fund`:
    - Check if fund exists by name
    - If exists: return existing fund
    - If not: create new fund with category, inception_date
    - Return fund object
  - `get_fund_by_name(name: str, session) -> Optional[Fund]`
  - `get_fund_by_id(id: int, session) -> Optional[Fund]`
  - `list_funds(session) -> List[Fund]`
- Error handling: descriptive exceptions for DB errors

**Acceptance Criteria:**

- ✓ Can create fund with name and category
- ✓ Duplicate fund names return existing fund (idempotent)
- ✓ Can query by name or id
- ✓ Unit tests pass: `pytest -m unit tests/test_fund_repo.py`

---

#### Task 4.3: Nav History Repository

**Effort:** Medium | **Depends on:** Task 1.4, Task 4.1

**Description:**

- Create `src/database/repositories/nav_repo.py` with `NavHistoryRepository` class
- Implement methods:
  - `create_nav_entry(fund_id: int, date: str, nav: Decimal, session) -> NavHistory`:
    - Creates new NavHistory entry
    - Enforces UNIQUE(fund_id, date) — catch violation and raise descriptive error
  - `get_nav_by_fund_and_date(fund_id: int, date: str, session) -> Optional[NavHistory]`
  - `get_nav_history_by_fund(fund_id: int, session) -> List[NavHistory]` (sorted by date)
  - `delete_nav_entry(id: int, session) -> bool` (if needed for duplicate resolution)
  - `check_duplicate(fund_id: int, date: str, session) -> bool` — returns True if entry exists
- Error handling: catch UNIQUE constraint violations, raise `DuplicateEntryError`

**Acceptance Criteria:**

- ✓ Can create nav entry
- ✓ Cannot create duplicate (fund_id, date) — raises error
- ✓ Can query by fund_id and date
- ✓ Can list nav history for a fund (sorted by date)
- ✓ Unit tests pass: `pytest -m unit tests/test_nav_repo.py`

---

### Group 5: Upload & Async Infrastructure (Wave 3)

#### Task 5.1: File Upload Endpoint

**Effort:** Medium | **Depends on:** Task 1.1, Task 2.3, Task 3.1

**Description:**

- Create `src/api/upload.py` with FastAPI router
- Implement `POST /upload` endpoint:
  - Accept multipart file upload (CSV or Excel)
  - Generate unique `job_id` (UUID)
  - Create staging directory: `{STAGING_DIR}/{job_id}/`
  - Save uploaded file to staging directory
  - Create UploadJob record in database (status: "processing")
  - Trigger async background task: `process_upload(job_id)`
  - Return immediately with HTTP 202 Accepted + job_id
  - Response: `{"job_id": "xxx", "status": "processing"}`
- Request validation:
  - Accept file types: .csv, .xlsx only
  - Check file size (reject >100MB for MVP)
  - Validate multipart form data
- Error handling:
  - Invalid file type → 400 Bad Request
  - File too large → 413 Payload Too Large
  - Storage error → 500 Internal Server Error
- Add logging for upload events

**Acceptance Criteria:**

- ✓ Can upload valid_complete.csv → returns 202 + job_id
- ✓ Can upload .xlsx file → same behavior
- ✓ Rejects .json file → 400 error
- ✓ File saved to staging directory
- ✓ UploadJob created in database with "processing" status
- ✓ Response includes job_id for status polling
- ✓ Integration tests pass: `pytest -m integration tests/test_upload_endpoint.py`

---

#### Task 5.2: Job State Management

**Effort:** Small | **Depends on:** Task 1.4

**Description:**

- Create `src/ingestion/job_manager.py` with `JobManager` class
- Implement in-memory job state for MVP (upgrade to Redis/Celery in Phase 2):
  - `jobs: Dict[str, JobState]` — in-memory dictionary
  - JobState dataclass: id, status ("processing", "completed", "failed"), imported_count, rejected_count, errors, created_at, updated_at
- Implement methods:
  - `create_job(job_id: str) -> JobState` — initialize job state
  - `get_job(job_id: str) -> Optional[JobState]`
  - `update_job(job_id: str, status, imported_count, rejected_count, errors) -> JobState`
  - `complete_job(job_id: str, imported_count, rejected_count, errors) -> JobState`
  - `fail_job(job_id: str, error_message) -> JobState`
- Persist to database:
  - JobState updates written to UploadJob table
  - On startup, load job states from database for recovery

**Acceptance Criteria:**

- ✓ Can create and track job states
- ✓ Job state persisted to UploadJob table
- ✓ Job state retrievable by job_id
- ✓ Unit tests pass

---

#### Task 5.3: Status Polling Endpoint

**Effort:** Medium | **Depends on:** Task 5.1, Task 5.2

**Description:**

- Create `src/api/status.py` with FastAPI router
- Implement `GET /status/{job_id}` endpoint:
  - Query JobManager for job_id
  - If job not found: return 404 Not Found
  - Return job state with current progress
  - Response JSON:
    ```json
    {
      "job_id": "xxx",
      "status": "completed",
      "imported_count": 10,
      "rejected_count": 0,
      "errors": [],
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T10:01:30Z"
    }
    ```
  - On "completed" status: include summary + any error details
  - On "failed" status: include error reason
- Error responses:
  - 404: job_id not found
  - 500: database query error

**Acceptance Criteria:**

- ✓ Can poll status while processing
- ✓ Returns accurate imported/rejected counts
- ✓ Returns detailed error list for rejected rows
- ✓ Returns 404 for invalid job_id
- ✓ Integration tests pass: `pytest -m integration tests/test_status_endpoint.py`

---

#### Task 5.4: File Staging & Cleanup

**Effort:** Small | **Depends on:** Task 5.1

**Description:**

- Create `src/ingestion/staging.py` with `StagingManager` class
- Implement methods:
  - `create_staging_dir(job_id: str) -> Path` — creates {STAGING_DIR}/{job_id}/
  - `save_file(job_id: str, file_path: Path) -> Path` — copy file to staging dir
  - `cleanup_job(job_id: str) -> bool` — delete staging directory after processing
  - `cleanup_expired() -> int` — find staged files older than TTL (default 7 days), delete, return count
- Implement TTL cleanup task:
  - Scheduled task that runs daily (or on app startup)
  - Finds all staging directories older than STAGING_TTL_DAYS
  - Deletes old directories + updates UploadJob status
- Error handling:
  - File not found, permission errors, etc.
  - Log cleanup activities

**Acceptance Criteria:**

- ✓ Can create staging directory
- ✓ Can save file to staging
- ✓ Can cleanup after processing
- ✓ TTL cleanup removes old files
- ✓ Unit tests pass

---

### Group 6: Upload Processing Pipeline (Wave 4)

#### Task 6.1: Async Upload Processor

**Effort:** Large | **Depends on:** Task 2.3, Task 3.1, Task 3.2, Task 5.2, Task 6.2, Task 6.3

**Description:**

- Create `src/ingestion/processor.py` with `UploadProcessor` class
- Implement `process_upload_async(job_id: str)` function (async, runs in background task):
  - Retrieve staged file from {STAGING_DIR}/{job_id}/
  - Update job status: "processing" → "parsing"
  - Call `parse_file(staged_file_path)` → get list of (row_num, row_dict) tuples
  - Update job status: "parsing" → "validating"
  - For each row:
    - Call `DataValidator.validate_row(row_dict, row_num)`
    - Collect valid rows and error details separately
  - Update job status: "validating" → "duplicate_check"
  - Call `DuplicateDetector.detect_duplicates(valid_rows)` → get duplicates in file
  - Call `DuplicateDetector.detect_duplicates_in_database(valid_rows, db_session)` → get database conflicts
  - If duplicates found:
    - Log duplicates
    - Update job with duplicate_resolution_needed flag
    - Return job status "awaiting_resolution" (user must resolve via web UI or API)
  - If no duplicates (or user resolved them):
    - Update job status: "duplicate_check" → "storing"
    - For each valid, non-duplicate row:
      - Call `FundRepository.create_or_get_fund()`
      - Call `NavHistoryRepository.create_nav_entry()`
    - On constraint violation (shouldn't happen if duplicate check passed): log and skip
  - Update job status: "storing" → "completed"
  - Populate job with:
    - `imported_count` = number of rows successfully stored
    - `rejected_count` = number of rows failed validation + skipped duplicates
    - `errors` = list of ErrorDetail objects
  - Call `StagingManager.cleanup_job(job_id)` — delete staged files
  - Persist job state to database
- Error handling:
  - If any step fails (file read, database error, etc.), update job status to "failed" with error message
  - Log full stack trace at ERROR level
  - Do NOT crash the background task runner

**Acceptance Criteria:**

- ✓ Can process valid_complete.csv → 10 rows stored, 0 rejected, status "completed"
- ✓ Can process valid_partial.csv → all rows stored (nulls allowed)
- ✓ Can process invalid_negative_nav.csv → 0 rows stored, 5 rejected, errors populated
- ✓ Can detect in-file duplicates from valid_with_duplicates.csv → status "awaiting_resolution"
- ✓ Job state persisted to database
- ✓ Staged files cleaned up after successful processing
- ✓ Staged files cleaned up on error
- ✓ Background task does not crash on errors (graceful degradation)
- ✓ Integration tests pass: `pytest -m integration tests/test_upload_processor.py`

---

#### Task 6.2: Duplicate Resolution Handler

**Effort:** Medium | **Depends on:** Task 1.3, Task 4.3

**Description:**

- Create `src/ingestion/duplicate_resolver.py` with `DuplicateResolver` class
- Implement `resolve_duplicates(job_id: str, resolutions: Dict[str, str], db_session)` method:
  - Resolutions format: {"fund_name,date": "update"|"delete", ...}
  - "update" = keep second entry, overwrite first
  - "delete" = skip second entry, keep first
  - For each resolution:
    - Find affected rows from job's rejected list
    - Execute resolution (update or delete)
    - Move rows from rejected to imported (if update/keep)
  - Update job state with new imported/rejected counts
  - Mark duplicates as resolved in job record
- User must provide resolutions via API endpoint (implemented in next task)

**Acceptance Criteria:**

- ✓ Can resolve in-file duplicates (update/delete)
- ✓ Updates job imported/rejected counts
- ✓ Persists resolutions to database
- ✓ Unit tests pass

---

#### Task 6.3: Duplicate Resolution Endpoint

**Effort:** Small | **Depends on:** Task 5.3, Task 6.2

**Description:**

- Create `src/api/duplicates.py` with FastAPI router
- Implement `POST /duplicates/{job_id}/resolve` endpoint:
  - Request body: `{"resolutions": {"fund_name,date": "update"|"delete", ...}}`
  - Retrieve job by job_id
  - Check job status is "awaiting_resolution" (else return 409 Conflict)
  - Call `DuplicateResolver.resolve_duplicates(job_id, resolutions, db_session)`
  - Resume async processing (continue import after duplicate resolution)
  - Return updated job state
- Error handling:
  - 404: job_id not found
  - 409: job not in "awaiting_resolution" status
  - 400: invalid resolutions format

**Acceptance Criteria:**

- ✓ Can resolve duplicates via API
- ✓ Job resumes processing after resolution
- ✓ Job completes with correct imported/rejected counts
- ✓ Integration tests pass: `pytest -m integration tests/test_duplicate_resolution_endpoint.py`

---

### Group 7: Error Handling & User Feedback (Wave 4)

#### Task 7.1: Error Response Schema

**Effort:** Small | **Depends on:** Task 1.3

**Description:**

- Create `src/schemas/errors.py` with error response schemas:
  - `ErrorDetail` (row_number, field, error_message, value)
  - `UploadErrorResponse` (job_id, status, imported_count, rejected_count, errors: List[ErrorDetail])
  - `DuplicateDetail` (fund_name, date, row_numbers: List[int])
  - `DuplicateErrorResponse` (job_id, duplicates: List[DuplicateDetail])
- Ensure error messages are user-friendly and actionable
- Include data values in error responses (helps user debug)

**Acceptance Criteria:**

- ✓ Schemas defined and used in API responses
- ✓ Error messages are clear and specific
- ✓ Unit tests pass

---

#### Task 7.2: Logging & Monitoring

**Effort:** Small | **Depends on:** Task 1.1

**Description:**

- Create `src/logging_config.py`:
  - Configure logging for entire application
  - Log levels: DEBUG (dev), INFO (processing events), WARNING (validation issues), ERROR (failures)
  - Log format: timestamp, level, module, message
  - File logging to `logs/ingestion.log` (rotate daily)
  - Console logging (for development)
  - Configure log level from env var: `LOG_LEVEL`
- Add logging calls throughout:
  - Parse start/completion
  - Validation pass/fail per row
  - Database operations (create fund, create nav entry, constraint violations)
  - Job state transitions
  - Error events
- Ensure sensitive data (passwords, API keys) never logged

**Acceptance Criteria:**

- ✓ Logging configured in FastAPI startup
- ✓ Log files created and rotated
- ✓ Key events logged at appropriate levels
- ✓ No sensitive data in logs

---

### Group 8: FastAPI App & Integration (Wave 4)

#### Task 8.1: Main FastAPI Application

**Effort:** Small | **Depends on:** Task 5.1, Task 5.3, Task 6.3

**Description:**

- Create `src/main.py` with FastAPI app:
  - Initialize FastAPI app: `app = FastAPI(title="FundLens Ingestion", version="1.0")`
  - Register routers:
    - `/api/upload` (Task 5.1)
    - `/api/status` (Task 5.3)
    - `/api/duplicates` (Task 6.3)
  - Startup event: initialize database, load schema config, start TTL cleanup scheduler
  - Add global exception handler for unhandled exceptions → 500 response with job_id context
  - Add middleware for request logging
- Create `src/config.py` with configuration:
  - Load from env vars: DATABASE_URL, STAGING_DIR, STAGING_TTL_DAYS, LOG_LEVEL
  - Load schema config from `config/schema.json`
  - Defaults for all env vars

**Acceptance Criteria:**

- ✓ `uvicorn src.main:app --reload` starts successfully
- ✓ Routers registered and available
- ✓ Startup events run without errors
- ✓ `/docs` endpoint shows Swagger UI with all endpoints

---

#### Task 8.2: Background Task Runner

**Effort:** Small | **Depends on:** Task 8.1

**Description:**

- Implement background task integration in FastAPI:
  - Upload endpoint uses `BackgroundTasks.add_task(process_upload_async, job_id)` to queue async work
  - FastAPI runs background tasks in thread pool (sufficient for MVP)
  - Ensure async processor is non-blocking and thread-safe
- For production upgrade path (Phase 2+):
  - Document migration to Celery + Redis
  - Prepare processor code to be framework-agnostic

**Acceptance Criteria:**

- ✓ Upload triggers background task
- ✓ Endpoint returns immediately (202)
- ✓ Background task runs to completion
- ✓ Job state updated in database

---

### Group 9: Testing & Verification (Wave 5)

#### Task 9.1: Unit Tests — Parsers & Validators

**Effort:** Medium | **Depends on:** Task 2.1, Task 2.2, Task 3.1, Task 3.2

**Description:**

- Create comprehensive unit tests in `tests/test_parsers.py`:
  - `test_csv_parser_valid_complete()` — parse valid_complete.csv
  - `test_csv_parser_valid_partial()` — parse valid_partial.csv
  - `test_csv_parser_encoding_utf8()` — parse utf8_encoding.csv
  - `test_csv_parser_encoding_latin1()` — parse latin1_encoding.csv
  - `test_csv_parser_empty()` — parse empty.csv
  - `test_csv_parser_file_not_found()` — error handling
  - `test_excel_parser_valid()` — parse Excel file
  - `test_excel_parser_multiple_sheets()` — select sheet
  - `test_excel_parser_dates_converted()` — Excel dates to ISO-8601
- Create `tests/test_validators.py`:
  - `test_validate_row_valid()` — pass valid row
  - `test_validate_row_missing_required_field()` — fail on missing required field
  - `test_validate_row_invalid_date_format()` — fail on bad date
  - `test_validate_row_negative_nav()` — fail on negative NAV
  - `test_validate_row_field_mapping()` — test CSV column name mapping
  - `test_validate_row_error_message_quality()` — error message is user-friendly
- Create `tests/test_duplicate_detector.py`:
  - `test_detect_duplicates_in_file()` — detect valid_with_duplicates.csv
  - `test_detect_duplicates_empty_list()` — no duplicates in valid_complete.csv
  - `test_detect_duplicates_database()` — detect conflicts with seeded database
- Coverage target: >90% for parsers, validators, detectors

**Acceptance Criteria:**

- ✓ All unit tests pass: `pytest -m unit tests/test_*.py`
- ✓ Coverage report: >90% for core parsing/validation logic
- ✓ No test flakiness

---

#### Task 9.2: Integration Tests — End-to-End Pipeline

**Effort:** Large | **Depends on:** Task 8.1, Task 9.1

**Description:**

- Create `tests/test_integration.py` with full pipeline tests:
  - **Test Suite 1: Happy Path**
    - `test_upload_parse_validate_store_complete()` — upload valid_complete.csv, verify all 10 rows stored
    - `test_upload_parse_validate_store_partial()` — upload valid_partial.csv, verify all stored with nulls
    - `test_status_polling()` — upload, poll status multiple times, verify completion
  - **Test Suite 2: Validation Errors**
    - `test_upload_invalid_dates()` — upload invalid_bad_dates.csv, verify rows rejected
    - `test_upload_invalid_nav()` — upload invalid_negative_nav.csv, verify rows rejected
    - `test_upload_missing_fields()` — upload invalid_missing_fields.csv, verify detailed error reports
    - `test_error_details_accuracy()` — verify error messages match spec (row number, field, value)
  - **Test Suite 3: Duplicates**
    - `test_detect_in_file_duplicates()` — upload valid_with_duplicates.csv, verify "awaiting_resolution" status
    - `test_resolve_duplicates_update()` — resolve with "update" option, verify row stored
    - `test_resolve_duplicates_delete()` — resolve with "delete" option, verify row skipped
  - **Test Suite 4: Database Integrity**
    - `test_unique_constraint_fund_date()` — attempt duplicate store, verify UNIQUE constraint prevents it
    - `test_foreign_key_fund()` — verify nav_history entries reference valid funds
  - **Test Suite 5: Edge Cases**
    - `test_upload_empty_file()` — upload empty.csv, verify handled gracefully
    - `test_upload_very_large_file()` — test with 1000+ rows (or mock)
    - `test_concurrent_uploads()` — simulate 2-3 concurrent uploads, verify no conflicts
- Use test database with Alembic migrations applied
- Each test: setup fixture → execute → verify database state + API responses
- Cleanup: rollback test database after each test

**Acceptance Criteria:**

- ✓ All integration tests pass: `pytest -m integration tests/test_integration.py`
- ✓ Test database is clean after each test
- ✓ Database queries verify correct rows stored
- ✓ API responses match spec (status codes, JSON format)
- ✓ Error handling works end-to-end
- ✓ No data corruption under load

---

#### Task 9.3: API Contract Tests

**Effort:** Medium | **Depends on:** Task 8.1

**Description:**

- Create `tests/test_api_contract.py`:
  - **Upload Endpoint Tests**
    - `test_upload_accepts_csv()` — POST /upload with CSV, verify 202 response
    - `test_upload_accepts_xlsx()` — POST /upload with Excel, verify 202 response
    - `test_upload_rejects_json()` — POST /upload with JSON, verify 400 error
    - `test_upload_response_format()` — verify response JSON has job_id, status fields
    - `test_upload_file_too_large()` — >100MB file, verify 413 error
  - **Status Endpoint Tests**
    - `test_status_processing()` — get status during processing, verify "processing" status
    - `test_status_completed()` — get status after completion, verify "completed" + counts
    - `test_status_failed()` — get status for failed job, verify "failed" + error
    - `test_status_not_found()` — get status for invalid job_id, verify 404
    - `test_status_response_format()` — verify response JSON structure
  - **Duplicate Endpoint Tests**
    - `test_duplicate_resolution_update()` — POST /duplicates/{job_id}/resolve with "update", verify job resumes
    - `test_duplicate_resolution_delete()` — POST /duplicates/{job_id}/resolve with "delete", verify job resumes
    - `test_duplicate_resolution_wrong_status()` — resolve on completed job, verify 409 error
    - `test_duplicate_resolution_invalid_job_id()` — resolve on non-existent job, verify 404
- Use FastAPI TestClient for API testing
- Verify response codes, content-type headers, JSON structure

**Acceptance Criteria:**

- ✓ All API contract tests pass
- ✓ Response codes match spec
- ✓ Response JSON structure matches spec
- ✓ Error handling per spec

---

#### Task 9.4: Test Fixture Validation

**Effort:** Small | **Depends on:** Task 1.5

**Description:**

- Create `tests/validate_fixtures.py`:
  - Parse all fixture files and validate structure
  - Verify `valid_complete.csv` has exactly 10 valid rows
  - Verify `valid_partial.csv` has optional fields with nulls
  - Verify `valid_with_duplicates.csv` has 2 duplicate pairs at known row numbers
  - Verify `invalid_*.csv` files have expected errors at expected rows
  - Print fixture summary on test collection

**Acceptance Criteria:**

- ✓ All fixtures present and valid
- ✓ `pytest tests/validate_fixtures.py` passes
- ✓ Fixture summary printed clearly

---

### Group 10: Documentation & Demo (Wave 5)

#### Task 10.1: API Documentation

**Effort:** Small | **Depends on:** Task 8.1

**Description:**

- Add docstrings to all API endpoints (FastAPI auto-generates `/docs`)
- Create `docs/API.md`:
  - **Upload Endpoint**
    - Description, HTTP method, URL, request format, response format
    - Example curl command
    - Error responses
  - **Status Endpoint**
    - Description, HTTP method, URL, query params, response format
    - Example responses (processing, completed, failed)
  - **Duplicate Resolution Endpoint**
    - Description, HTTP method, URL, request format
    - Example resolutions JSON
- Document schema configuration in `docs/schema_configuration.md`:
  - How to modify `config/schema.json`
  - Field mapping example
  - Required vs optional fields

**Acceptance Criteria:**

- ✓ FastAPI `/docs` shows all endpoints with descriptions
- ✓ `docs/API.md` has examples and error codes
- ✓ `docs/schema_configuration.md` explains configuration

---

#### Task 10.2: Developer Setup Guide

**Effort:** Small | **Depends on:** Task 1.1, Task 1.2

**Description:**

- Create `docs/DEVELOPMENT.md`:
  - Prerequisites: Python 3.9+, PostgreSQL, pip
  - Setup steps:
    1. `pip install -r requirements.txt`
    2. Create `.env` from `.env.example`
    3. `alembic upgrade head`
    4. `uvicorn src.main:app --reload`
  - Running tests: `pytest -m unit`, `pytest -m integration`, `pytest`
  - Directory structure explanation
  - Logging and debugging tips

**Acceptance Criteria:**

- ✓ `docs/DEVELOPMENT.md` is complete and current
- ✓ Following guide successfully sets up dev environment

---

#### Task 10.3: Demo & Verification Walkthrough

**Effort:** Medium | **Depends on:** Task 9.2, Task 10.1

**Description:**

- Create `docs/DEMO.md` with step-by-step demo:
  1. Start app: `uvicorn src.main:app --reload`
  2. Upload valid_complete.csv via curl: `curl -F "file=@tests/fixtures/valid_complete.csv" http://localhost:8000/api/upload`
  3. Note job_id
  4. Poll status: `curl http://localhost:8000/api/status/{job_id}`
  5. Verify 10 rows stored in PostgreSQL: `select count(*) from nav_history;`
  6. Upload invalid_negative_nav.csv, verify error report
  7. Upload valid_with_duplicates.csv, verify "awaiting_resolution" status
  8. Resolve duplicates: `curl -X POST http://localhost:8000/api/duplicates/{job_id}/resolve ...`
  9. Verify completion
- Include expected outputs for each step

**Acceptance Criteria:**

- ✓ `docs/DEMO.md` is complete
- ✓ Demo successfully runs through all scenarios
- ✓ All requirements verified by demo

---

## Requirements Coverage

| Requirement                                | Task(s)                       | Status    |
| ------------------------------------------ | ----------------------------- | --------- |
| REQ-001: Accept CSV files                  | Task 2.1, Task 8.1            | ✓ Covered |
| REQ-002: Accept Excel files                | Task 2.2, Task 8.1            | ✓ Covered |
| REQ-003: Normalize diverse formats         | Task 1.3, Task 3.1, Task 2.3  | ✓ Covered |
| REQ-004: Validate data quality             | Task 3.1, Task 3.2, Task 6.1  | ✓ Covered |
| REQ-005: User upload through web interface | Task 5.1, Task 8.1, Task 10.3 | ✓ Covered |

---

## Effort Estimation

### Per-Group Breakdown

| Group                    | Tasks        | Effort                        | Estimate (hrs)  |
| ------------------------ | ------------ | ----------------------------- | --------------- |
| 1. Setup                 | 5            | 5 Small/Medium                | 20-25           |
| 2. Parsing               | 3            | 2 Medium + 1 Small            | 15-18           |
| 3. Validation            | 2            | 2 Medium                      | 15-18           |
| 4. Database Layer        | 3            | 1 Small + 2 Medium            | 12-15           |
| 5. Upload Infrastructure | 4            | 1 Medium + 2 Small + 1 Medium | 18-22           |
| 6. Processing Pipeline   | 3            | 1 Large + 2 Medium            | 25-30           |
| 7. Error Handling        | 2            | 2 Small                       | 8-10            |
| 8. FastAPI App           | 2            | 1 Small + 1 Small             | 10-12           |
| 9. Testing               | 4            | 2 Medium + 1 Large + 1 Small  | 25-30           |
| 10. Documentation        | 3            | 3 Small                       | 10-12           |
| **TOTAL**                | **31 Tasks** |                               | **158-192 hrs** |

### Timeline Estimate (Single Developer, Full-Time)

- **Wave 1 (Setup & Foundation):** 1 week (20-25 hours) — tasks run in parallel
- **Wave 2 (Parsing & Validation):** 1 week (18-22 hours) — tasks run in parallel
- **Wave 3 (Async Infrastructure):** 0.5 week (18-22 hours) — tasks in parallel
- **Wave 4 (Pipeline Integration):** 1 week (25-30 hours) — sequential but short duration
- **Wave 5 (Testing & Documentation):** 1 week (35-42 hours) — heavy testing phase
- **Total Duration:** 4-4.5 weeks (accelerated with parallelization, quality focus)

**Parallelization Strategy:**

- Wave 1: All 5 tasks in parallel → 1 person can complete in parallel lanes
- Wave 2: CSV/Excel/Validation tasks in parallel, Database tasks sequential within the wave
- Wave 3: Upload/Status/Staging in parallel
- Wave 4: Processor/Resolver/Endpoint can partly overlap
- Wave 5: Unit/Integration tests in parallel

**For 2-3 Week Target (Aggressive):**

- Focus on core path: Tasks 1.1-1.4, 2.1-2.3, 3.1-3.2, 5.1, 5.2, 5.3, 6.1, 8.1, 9.2
- Defer: Advanced error handling (Task 7.2), full documentation (Task 10.1-10.3)
- Results: MVP works, most requirements met, but lacking polish

---

## Risk Assessment

### Risk 1: File Encoding Issues

**Severity:** Medium | **Probability:** High

**Description:** Users may upload CSV files with non-UTF-8 encoding (Latin-1, Windows-1252). Pandas may fail to parse or produce garbled data.

**Mitigation:**

- Implement encoding detection in CSV parser (Task 2.1)
- Test with multiple encodings (Task 9.4)
- Provide user-friendly error message if encoding detection fails
- Document supported encodings in API docs

---

### Risk 2: Large File Memory Usage

**Severity:** Medium | **Probability:** Medium

**Description:** Very large CSV files (>500MB) loaded entirely into memory by Pandas could cause OOM errors.

**Mitigation:**

- Implement file size check in upload endpoint (Task 5.1) — reject >100MB for MVP
- For Phase 2, implement streaming parser with chunked processing
- Monitor memory usage in tests (Task 9.2)
- Set resource limits on background task runner

---

### Risk 3: Concurrent Upload State Conflicts

**Severity:** Medium | **Probability:** Low

**Description:** Multiple concurrent uploads could have race conditions in job state management.

**Mitigation:**

- Job IDs are UUIDs (collision-free)
- Database isolation at transaction level prevents conflicts
- Test concurrent uploads in integration tests (Task 9.2)
- Document concurrency model in dev guide

---

### Risk 4: PostgreSQL Constraint Violations

**Severity:** Low | **Probability:** High

**Description:** UNIQUE constraint on (fund_id, date) could cause import failures if duplicate detection misses.

**Mitigation:**

- Comprehensive duplicate detection tests (Task 9.1)
- Catch constraint violations gracefully in processor (Task 6.1)
- Log detailed error with row info for debugging
- Error message explains constraint and suggests resolution

---

### Risk 5: Schema Configuration Errors

**Severity:** Medium | **Probability:** Low

**Description:** Misconfigured `config/schema.json` could cause parsing failures (missing required fields, incorrect field names).

**Mitigation:**

- Schema configuration validation on app startup (Task 8.1)
- Clear error messages if configuration invalid
- Example `schema.json` with documentation
- Schema validation tests (Task 9.1)

---

### Risk 6: Background Task Runner Crashes

**Severity:** High | **Probability:** Low

**Description:** Unhandled exceptions in background task could crash entire app or leave jobs in undefined state.

**Mitigation:**

- Comprehensive exception handling in processor (Task 6.1)
- All errors logged with full context
- Job state updated to "failed" with error message
- Separate background task from request handling (FastAPI BackgroundTasks)
- Integration tests for error scenarios (Task 9.2)

---

### Risk 7: Database Connection Pool Exhaustion

**Severity:** Medium | **Probability:** Low

**Description:** Many concurrent uploads could exhaust connection pool.

**Mitigation:**

- Configure connection pooling in SQLAlchemy (Task 4.1)
- Limit concurrent uploads (documented in deployment guide)
- Monitor connection usage in tests
- Phase 2: upgrade to async database driver

---

## Verification Checklist

### Requirement Verification

- [ ] **REQ-001:** Test CSV upload with valid_complete.csv, verify 10 rows parsed and stored
- [ ] **REQ-002:** Test Excel upload with valid_complete.xlsx, verify 10 rows parsed and stored
- [ ] **REQ-003:** Test schema mapping (e.g., "Fund Name" → "fund_name"), verify fields normalized correctly
- [ ] **REQ-004:** Test validation with invalid_negative_nav.csv, verify rejected rows reported with reasons; test duplicate detection with valid_with_duplicates.csv, verify duplicates identified
- [ ] **REQ-005:** Test web upload via `/api/upload` endpoint, verify file upload and job tracking works

### Quality Verification

- [ ] Unit test coverage >90% for parsers, validators, detectors
- [ ] Integration tests cover: happy path, validation errors, duplicates, database integrity
- [ ] API contract tests verify response codes and formats
- [ ] Edge case tests: empty files, encoding, large files, concurrent uploads
- [ ] All error messages are user-friendly and actionable
- [ ] Logging is comprehensive without exposing sensitive data
- [ ] Database schema matches requirements (UNIQUE constraints, foreign keys, indexes)
- [ ] Background task processor handles errors gracefully

### Performance Verification

- [ ] Upload endpoint returns 202 immediately (async processing verified)
- [ ] Status polling endpoint responds <500ms
- [ ] Parsing 1000+ rows completes in reasonable time (<30 seconds)
- [ ] Database queries for stored data use indexes (explain plan shows index usage)

### Documentation Verification

- [ ] API docs available at `/docs` with all endpoints documented
- [ ] `docs/API.md` has examples and error codes
- [ ] `docs/DEVELOPMENT.md` allows clean setup from scratch
- [ ] `docs/DEMO.md` successfully runs through all scenarios
- [ ] Schema configuration documented and configurable

---

## Next Steps After Phase 1

### Phase 2: Storage & Retrieval Infrastructure

- Implement FAISS vector store for semantic search
- Create retrieval layer querying PostgreSQL + FAISS
- Add data aggregation endpoints (fund performance metrics)
- Implement context assembly for LLM queries

### Phase 2+ Improvements to Phase 1

- Upgrade to Celery + Redis for background job processing (replaces FastAPI BackgroundTasks)
- Implement streaming CSV parser for large files
- Add database connection pooling monitoring
- Add audit logging for all data modifications

### Known Limitations in MVP

- Single-user system (no authentication)
- No scheduled ingestion (manual uploads only)
- No data versioning or rollback capability
- No resumable uploads for very large files
- Job state stored in-memory (not persistent across app restarts in Wave 1 MVP)

---

## Success Criteria for Phase 1 Completion

**Phase 1 is complete when:**

1. ✓ All 31 tasks implemented and tested
2. ✓ All 5 requirements (REQ-001 through REQ-005) verified working
3. ✓ CSV and Excel files can be uploaded and processed
4. ✓ Data normalized to unified schema and stored in PostgreSQL
5. ✓ Validation works: valid rows imported, invalid rows reported with details
6. ✓ Duplicates detected in-file and in database; user prompted for resolution
7. ✓ Async job processing works: upload returns immediately, status polling works
8. ✓ Error handling is comprehensive: all error paths tested, user messages clear
9. ✓ Test suite passes: unit tests >90% coverage, integration tests comprehensive
10. ✓ Documentation complete: API docs, dev setup, demo guide
11. ✓ Demo walkthrough successfully shows all features

---

**Created:** 2026-04-27  
**Status:** Ready for Execution  
**Executor:** Single developer or development team  
**Timeline:** 4-4.5 weeks at full-time sprint, or 2-3 weeks with aggressive parallelization and deferred polish
