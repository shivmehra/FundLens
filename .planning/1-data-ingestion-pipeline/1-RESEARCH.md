# Phase 1: Data Ingestion Pipeline — Technical Research

**Research Date:** 2026-04-26  
**Status:** Complete  
**Focus Areas:** File parsing, async job processing, schema validation, database design

---

## 1. File Parsing Strategies (CSV & Excel)

### CSV Parsing

**Best Practice:** Use Pandas for CSV parsing — it's the industry standard for data engineering in Python.

**Why:**

- Handles encoding issues automatically (UTF-8, Latin-1, etc.)
- Efficient memory usage for chunked reading
- Built-in type inference and data validation
- Easy integration with Pydantic for downstream validation

**Code Pattern:**

```python
import pandas as pd

df = pd.read_csv(uploaded_file.file, dtype=str)  # Read as strings first for validation
# Then validate types explicitly via Pydantic
```

**Pitfalls to avoid:**

- Auto type-coercion can hide data quality issues — read as strings first, validate explicitly
- Large files (>100MB) → use `chunksize` parameter for chunked reading
- Encoding detection → always specify `encoding='utf-8'` explicitly in production

### Excel Parsing

**Best Practice:** Use `openpyxl` (for .xlsx) or `xlrd` (for .xls).

**Why:**

- `openpyxl`: Modern, handles formulas/formatting, streaming mode for large files
- `xlrd`: Legacy but simpler for read-only .xls files
- Pandas can wrap either with `pd.read_excel()` — recommended for consistency

**Code Pattern:**

```python
df = pd.read_excel(uploaded_file.file, sheet_name=0, dtype=str)  # Same pattern as CSV
```

**Pitfalls to avoid:**

- Excel files may have headers in row 2, not row 1 → inspect first rows manually
- Formulas render as values; no way to access the formula itself
- Large .xlsx files (>50MB) → use streaming mode (`openpyxl.load_workbook(data_only=True)`)

---

## 2. Schema Validation Patterns

### Pydantic v2 for Flexible Schemas

**Best Practice:** Use Pydantic v2 for schema definition and validation.

**Why:**

- Type-safe validation with clear error messages
- Supports custom validators for business logic (e.g., date range, positive NAV)
- Can be configured dynamically (field required/optional at runtime)
- Serialization to/from JSON, ORM models

**Dynamic Schema Pattern (your requirement):**

```python
from pydantic import BaseModel, Field, validator

# Load from config file
SCHEMA_CONFIG = {
    "required_fields": ["fund_name", "date", "nav", "category"],
    "optional_fields": ["manager", "inception_date", ...],
    "field_transforms": {
        "Fund Name": "fund_name",  # CSV header → schema field
        "NAV": "nav"
    }
}

class FundRow(BaseModel):
    fund_name: str = Field(..., min_length=1)
    date: str = Field(...)  # Validate ISO-8601 in custom validator
    nav: Decimal = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    manager: Optional[str] = None

    @validator('date')
    def validate_date(cls, v):
        datetime.strptime(v, '%Y-%m-%d')  # Ensure ISO-8601
        return v
```

**Pitfalls:**

- Don't use `str` for numeric fields → use `Decimal` (exact arithmetic, no float precision loss)
- Custom validators must raise `ValueError` for Pydantic to catch them
- Field transformations (header mapping) happen BEFORE Pydantic validation

---

## 3. Async Job Processing for File Uploads

### FastAPI + BackgroundTasks vs Celery

**Choice for MVP:** FastAPI BackgroundTasks with simple in-memory queue.

**Why:**

- No external dependencies (Redis, Celery broker)
- Sufficient for <100MB files, single-instance deployments
- Easier debugging and local testing
- Can scale to Celery+Redis later

**Pitfalls:**

- BackgroundTasks don't persist across server restarts
- No job history/audit trail (log to file instead)
- For >1000 concurrent uploads → need distributed queue (Celery+Redis)

### Job State Management Pattern

```python
# In-memory dict for MVP (replace with Redis/DB in production)
job_store = {}

@app.post("/upload")
async def upload_file(file: UploadFile):
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "queued", "progress": 0}

    background_tasks.add_task(process_file, job_id, file)
    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return job_store.get(job_id, {"error": "not found"})

async def process_file(job_id: str, file: UploadFile):
    try:
        job_store[job_id]["status"] = "processing"
        # ... parse, validate, store
        job_store[job_id]["status"] = "completed"
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)
```

**Pitfalls:**

- Job store lost on restart → use persistent backend (database, Redis) even for MVP
- File cleanup → implement TTL-based deletion (7 days) to avoid disk buildup
- Status polling can hammer the API → implement exponential backoff on client

---

## 4. PostgreSQL Schema Design for Fund Data

### Tables & Relationships

**Normalization approach:**

```sql
-- Funds master table (immutable once created)
CREATE TABLE funds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50),
    inception_date DATE,
    manager VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- NAV history (many-to-one relationship)
CREATE TABLE nav_history (
    id SERIAL PRIMARY KEY,
    fund_id INT NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    nav DECIMAL(20, 4) NOT NULL CHECK (nav > 0),
    UNIQUE(fund_id, date),  -- Prevents duplicate entries for same fund on same date
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Phase 2 retrieval
CREATE INDEX idx_funds_name ON funds(name);
CREATE INDEX idx_nav_history_date ON nav_history(date);
CREATE INDEX idx_nav_history_fund_id ON nav_history(fund_id);
```

**Why this design:**

- Normalization prevents data duplication
- UNIQUE constraint on `(fund_id, date)` enforces no duplicate NAV per fund per date
- CASCADE delete keeps data consistent
- Indexes on commonly-queried columns

**Pitfalls:**

- Don't store NAV history as JSONB (non-queryable for Phase 2 retrieval)
- Insert performance: batch inserts via `executemany()` not one-by-one
- Date indexing: use DATE type, not TIMESTAMP (date-only queries are simpler)

---

## 5. Error Reporting & Logging

### Structured Error Format

**Pattern for Phase 1:**

```python
class ValidationError(BaseModel):
    row_number: int
    field_name: str
    actual_value: str
    error_reason: str
    severity: str  # "error" | "warning"

# Response shape:
{
    "imported_count": 95,
    "rejected_count": 5,
    "errors": [
        {
            "row_number": 42,
            "field_name": "nav",
            "actual_value": "abc",
            "error_reason": "Expected decimal, got string",
            "severity": "error"
        },
        ...
    ]
}
```

**Why:**

- User can pinpoint exactly where data failed
- Downstream can parse programmatically (not just display)
- Supports partial acceptance workflows

**Logging pattern:**

- Log all validations to file: `.logs/import_<date>.log`
- Include timestamps, job_id, file name, user, success/failure
- Keep logs for 30 days for audit trail

---

## 6. Testing Strategies

### Unit Tests (Validators, Parsers)

```python
# test_validators.py
def test_validate_date_iso8601():
    assert FundRow.parse_obj({"date": "2025-01-15", ...})
    with pytest.raises(ValidationError):
        FundRow.parse_obj({"date": "01/15/2025", ...})  # Wrong format

def test_validate_nav_positive():
    with pytest.raises(ValidationError):
        FundRow.parse_obj({"nav": "-100", ...})
```

### Integration Tests (File Upload → DB)

```python
# test_integration.py
def test_csv_upload_e2e(test_db):
    with open("tests/fixtures/valid.csv") as f:
        response = client.post("/upload", files={"file": f})
    job_id = response.json()["job_id"]

    # Poll status
    status = client.get(f"/status/{job_id}").json()
    assert status["imported_count"] == 10

    # Verify DB state
    funds = test_db.query(Fund).all()
    assert len(funds) == 10
```

### Fixtures (Committed to Repo)

- `tests/fixtures/valid_complete.csv` — 10 rows, all fields valid
- `tests/fixtures/valid_partial.csv` — 10 rows, optional fields missing
- `tests/fixtures/valid_with_duplicates.csv` — 10 rows, 2 duplicate fund+date pairs

---

## 7. Standard Stack Patterns & Project Conventions

### Why These Choices Fit Your Project

- **Pandas**: Your project is data-heavy; Pandas is the de facto standard for financial data processing in Python
- **Pydantic**: Pairs naturally with FastAPI; configurable schemas align with your requirement for extensibility
- **FastAPI**: Async-native, minimal boilerplate, excellent documentation for file uploads and background tasks
- **PostgreSQL**: Relational data (funds, NAV history) fit normalized schema; Phase 2 adds FAISS for semantic search

### Constraints to Honor (from CONTEXT.md)

- **Phase 1 owns schema creation** — your migration strategy (Alembic) must support versioning the schema changes
- **Async staging** — you chose local filesystem + polling; implement file cleanup (TTL) carefully to avoid disk exhaustion
- **Configurable schema** — use JSON or YAML config file (not hardcoded Python) for schema definitions; this enables Phase 2 changes without code redeploy

---

## 8. Common Pitfalls & Landmines

| Pitfall                                 | Impact                                       | Prevention                           |
| --------------------------------------- | -------------------------------------------- | ------------------------------------ |
| **Auto type-coercion**                  | Silent data loss (NaN values become strings) | Read as strings, validate explicitly |
| **Large file memory spikes**            | OOM during parsing                           | Use chunked reading for >50MB files  |
| **Job queue without persistence**       | Jobs lost on server restart                  | Add Redis/DB backend even for MVP    |
| **Duplicate detection after insertion** | Foreign key violations, data inconsistency   | Check duplicates BEFORE inserting    |
| **No error reporting**                  | User doesn't know what failed                | Implement row-level error details    |
| **Hardcoded schema**                    | Can't extend in Phase 2 without code changes | Externalize schema to config file    |

---

## 9. Validation Architecture (Nyquist Dimension 8)

### Verification Points for Phase 1

1. **Data quality metrics**: Row acceptance rate (target >90% for valid files)
2. **Schema compliance**: Every imported row matches schema exactly
3. **Duplicate detection**: All duplicate fund+date pairs identified and resolved
4. **Error reporting accuracy**: Error messages match actual validation failures
5. **Database consistency**: No orphaned records, foreign keys intact
6. **API contract**: Multipart upload returns job_id, /status endpoint works
7. **Async reliability**: Jobs complete regardless of server load
8. **Integration e2e**: CSV → parse → validate → PostgreSQL → query, all working

### Success Criteria for Verification

- [ ] Integration test passes (CSV → DB → query works)
- [ ] Duplicate detection test passes
- [ ] Error reporting test passes (malformed data produces correct error messages)
- [ ] API contract test passes (upload returns 202, status returns correct format)
- [ ] Database schema created with proper constraints

---

## 10. Dependencies & Integration Points

### Phase 2 Handoff

- **Database state**: PostgreSQL populated with fund data from Phase 1
- **Schema expectations**: `funds` and `nav_history` tables created, queryable
- **Data quality**: Phase 1 validates; Phase 2 trusts the data integrity

### Libraries to Investigate Before Planning

- `pandas[parquet,excel]` — CSV/Excel parsing
- `openpyxl` — Excel formula handling
- `pydantic[email]` — Schema validation
- `fastapi[standard]` — Async web framework
- `psycopg2-binary` or `asyncpg` — PostgreSQL driver
- `alembic` — Schema migrations
- `pytest` — Testing

---

## Key Decision Points for Planner

1. **Async Framework**: Celery+Redis (scalable but complex) vs FastAPI BackgroundTasks (simple, MVP-sufficient)?
   - **Recommendation**: FastAPI BackgroundTasks for MVP; note upgrade path to Celery

2. **Job State Persistence**: In-memory dict (lost on restart) vs Redis (persistent, requires infra) vs DB table (queryable)?
   - **Recommendation**: DB table for audit trail; Redis if you need sub-second polling performance

3. **Schema Configuration Format**: JSON vs YAML vs environment variables?
   - **Recommendation**: JSON file in `.config/schema.json` for easy deployment; YAML if you need comments

4. **Error Handling Philosophy**: Stop on first error vs collect all errors then report?
   - **Recommendation**: Collect all errors (your CONTEXT.md decision: partial acceptance + detailed report)

5. **Database Connection Pooling**: How many concurrent connections to PostgreSQL?
   - **Recommendation**: poolsize=5 for MVP (adjust based on load)

---

**Research Complete** — Ready for planning. Planner should reference this document for tech stack justification and pitfall avoidance.
