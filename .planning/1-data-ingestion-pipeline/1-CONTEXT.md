# Phase 1: Data Ingestion Pipeline — Implementation Context

**Phase Goal:** Build robust system to accept, validate, and normalize fund data from multiple file formats into PostgreSQL.

**Status:** Context locked. Ready for research and planning.

---

## Locked Implementation Decisions

### 1. Data Validation Philosophy

- **Choice**: Partial acceptance with detailed error reporting
- **Behavior**:
  - Valid rows imported to PostgreSQL
  - Invalid rows skipped with detailed error report (row numbers + validation failure reasons)
  - User receives structured feedback listing exactly which rows failed and why
- **Rationale**: Resilience for financial data — partial success is better than complete rejection, but transparency prevents silent data loss

---

### 2. Unified Schema Definition

- **Choice**: Flexible core schema with configurable required/optional fields
- **Required Fields** (must be present in any CSV/Excel for row to be valid):
  - `fund_name` (string, non-empty)
  - `date` (ISO-8601 format, YYYY-MM-DD)
  - `nav` (decimal, positive)
  - `category` (string, non-empty — e.g., "Equity", "Debt", "Hybrid")
- **Optional Fields** (enhancement; null values accepted):
  - `inception_date`, `manager`, `allocation`, `sharpe_ratio`, `max_drawdown`, `cagr`, `aum`
- **Critical Requirement**: Schema must be configurable (not hardcoded)
  - Future capability: User/admin can update which fields are required without code changes
  - Field transformation: System should support mapping source columns to schema fields (e.g., CSV "Fund Name" → schema `fund_name`)
- **Implication for Planning**: Schema configuration should live in a config file (JSON/YAML), not hardcoded Python constants

---

### 3. Duplicate Handling

- **Choice**: Detect and prompt user for resolution
- **Detection Key**: `(fund_name, date)` — if same fund on same date appears twice in CSV, it's a duplicate
- **User Prompt**: When duplicates detected, present options:
  - **Update**: Keep the second entry (overwrite first)
  - **Delete**: Skip the second entry (keep first)
- **Report**: List duplicates found so user knows what happened
- **Implication**: Validation logic must parse full file, then surface duplicates before persistence

---

### 4. File Upload Architecture

- **Choice**: Asynchronous staging with local filesystem
- **Flow**:
  1. User uploads CSV/Excel via web form
  2. FastAPI endpoint receives file, stores to local staging directory (`./uploads/staging/{job_id}/`)
  3. Endpoint returns immediately with `job_id` (HTTP 202 Accepted)
  4. Background async task processes file: parse, validate, detect duplicates, prompt/resolve, import to PostgreSQL
  5. User polls `/status/{job_id}` endpoint for progress and results
  6. Upon completion, staged file deleted, user sees: ✓ {N} rows imported, ⚠ {N} rows rejected (with details)
- **Status Endpoint** (`GET /status/{job_id}`):
  - Returns: `{ status: "processing|completed|failed", progress: 0-100, imported_count, rejected_count, errors: [list of error objects] }`
- **Staging Directory**: `./uploads/staging/` with auto-cleanup after 7 days (TTL configurable)
- **Implication for Planning**: Need background task runner (Celery/RQ recommended) or FastAPI BackgroundTasks

---

### 5. Data Storage in Phase 1

- **Choice**: Write normalized, validated data directly to PostgreSQL during Phase 1
- **Schema Ownership**: Phase 1 is responsible for creating PostgreSQL tables and indexes
- **Tables Phase 1 Creates**:
  - `funds` (id, name, category, inception_date, created_at, updated_at)
  - `nav_history` (id, fund_id, date, nav, created_at)
  - (Optionally: `fund_metadata` for optional fields like manager, allocation, etc.)
- **Constraints**:
  - Primary key: `funds.id`
  - Unique: `nav_history(fund_id, date)` — prevents duplicate nav entries
  - Foreign key: `nav_history.fund_id` → `funds.id`
  - Indexes on `funds.name`, `nav_history.date` for Phase 2 retrieval performance
- **Implication**: Phase 1 includes schema migrations (Alembic recommended) so schema can evolve safely

---

### 6. Testing Strategy

- **Choice**: Unit tests + integration tests with realistic fixtures
- **Fixture Files** (committed to repo under `tests/fixtures/`):
  1. **valid_complete.csv** — 10 complete rows, all fields valid, ready for import
  2. **valid_partial.csv** — 10 rows with optional fields missing (nulls OK), required fields present
  3. **valid_with_duplicates.csv** — 10 rows including 2 duplicate fund+date pairs (for testing duplicate detection)
- **Unit Tests**:
  - CSV/Excel parser: can parse files, extract rows
  - Validators: required field validation, type coercion, date parsing
  - Schema mapping: source columns → schema fields
- **Integration Tests**:
  - End-to-end: upload fixture file → validate → import to test PostgreSQL → query results
  - Error reporting: malformed file → error report generated correctly
  - Duplicate handling: duplicate detection works, user prompt surfaces correctly
- **Test Database**: Separate PostgreSQL instance (test_fundlens) for integration tests, reset between runs

---

## Requirements Traceability

| Requirement                                | Implementation Decision                                         | Status  |
| ------------------------------------------ | --------------------------------------------------------------- | ------- |
| REQ-001: Accept CSV files                  | Direct CSV parsing with Pandas; schema defined above            | Covered |
| REQ-002: Accept Excel files                | Pandas/openpyxl handles .xlsx; same schema mapping              | Covered |
| REQ-003: Normalize diverse formats         | Configurable schema + field transformation mapping              | Covered |
| REQ-004: Validate data quality             | Partial acceptance + detailed error report; duplicate detection | Covered |
| REQ-005: User upload through web interface | Async staging + status polling endpoint                         | Covered |

---

## Downstream Dependencies & Handoff

### For Phase 2 (Storage & Retrieval):

- ✓ PostgreSQL now populated with fund data
- ✓ `nav_history` table ready for historical queries
- ✓ Schema can be extended with FAISS embeddings table

### For Researchers:

- Study Pandas/openpyxl APIs for file parsing patterns
- Investigate Celery or FastAPI BackgroundTasks for async job handling
- Best practices for Pydantic schema validation with flexible required/optional fields

### For Planner:

- Estimate effort for: schema migrations, async task infrastructure, status polling endpoint, error reporting
- Identify risks: file encoding issues, large-file memory usage, concurrent upload limits
- Validate testability: can we create fixtures easily, can integration tests run reliably

---

## Open Questions for Planner/Researcher

1. **Async Job Framework**: Should we use Celery + Redis, or FastAPI BackgroundTasks + a job queue? (Trade-off: complexity vs scalability)
2. **File Encoding**: How should we handle non-UTF-8 CSV files? (Auto-detect vs require UTF-8)
3. **Staging Cleanup**: TTL strategy for old staged files — automatic deletion or manual cleanup?
4. **Concurrency**: What's the max concurrent uploads we target for MVP? (Affects staging directory design)

---

## Deferred Ideas (Backlog)

- Multi-user upload history/audit trail (Phase 5)
- Resumable uploads for very large files (beyond MVP)
- Automatic data quality scoring (e.g., "completeness index") per upload
- Data preview before final import (Phase 4, when UI exists)
- Scheduled CSV ingestion from URL or FTP (Phase 2+)

---

**Discussion locked**: 2026-04-26  
**Decisions finalized**: ✓ All 6 gray areas resolved  
**Next step**: Run `/gsd-plan-phase 1` to create detailed PLAN.md
