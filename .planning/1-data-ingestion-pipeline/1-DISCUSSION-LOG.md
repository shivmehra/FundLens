# Phase 1 Discussion Log

**Date**: 2026-04-26  
**Mode**: `--analyze` (trade-off analysis before each question)  
**Status**: ✓ All gray areas discussed, decisions locked

---

## Discussion Summary

### Gray Area 1: Data Validation Philosophy

**Question**: When a CSV has 100 rows and 5 are invalid (bad format, missing values), what should happen?

**Options Presented**:

- Reject entire file (all 100 rows rejected)
- Accept valid 95, report invalid 5 ⭐ **SELECTED**
- Try to fix invalid rows automatically

**Decision**: Partial acceptance with detailed error report (row-by-row errors)

**Follow-up**: How detailed should the error report be?

- Summary only (counts)
- Detailed (row-by-row errors) ⭐ **SELECTED**
- Detailed + exportable (row-by-row + rejected file)

**Locked Outcome**: Row-level error reporting with validation failure reasons

---

### Gray Area 2: Unified Schema Definition

**Question**: What should the normalized schema require as mandatory?

**Options Presented**:

- Minimal core (4 fields): name, date, nav, returns
- Recommended core (6 fields): +category, inception_date
- Full schema (10+ fields)

**User Response**: Flexible core (name, date, nav, category) + optional others ⭐ **FREEFORM**

**Context Captured**: User emphasized need for configurable schema + field transformation capability

**Follow-up**: When validating required fields, should a NULL value in 'nav' (required) cause rejection?

**User Response**: Strict validation, but wants configurable schema definition and field editing capability ⭐ **FREEFORM**

**Locked Outcome**: Strict validation for required fields; schema definition externalized to config file (not hardcoded)

---

### Gray Area 3: Duplicate Handling

**Question**: If the CSV has two rows for 'ICICI Equity Fund' on '2025-01-15', with different NAV values, what happens?

**Options Presented**:

- Reject (fund + date must be unique)
- Update (fund + date = merge point)

**User Response**: User should be given the option to update or delete ⭐ **FREEFORM**

**Locked Outcome**: Detect duplicates (fund_name + date), prompt user to choose: update (keep newer) or delete (keep first)

---

### Gray Area 4: File Upload Architecture

**Question**: For MVP, how should files be uploaded and processed?

**Options Presented**:

- Direct (synchronous)
- Staging (asynchronous) ⭐ **SELECTED** (recommended)
- Streaming (on-the-fly parsing)

**Follow-up 1**: Where should uploaded files be staged before validation/storage?

- Local filesystem ⭐ **SELECTED**
- Temporary database table
- In-memory (cache layer)

**Follow-up 2**: How should the upload API respond?

- Immediate ID + poll for results ⭐ **SELECTED**
- 202 Accepted + optional polling

**Locked Outcome**:

- Async staging to local filesystem (`./uploads/staging/{job_id}/`)
- Upload endpoint returns job_id immediately
- User polls `/status/{job_id}` for progress/results
- Background async task processes file

---

### Gray Area 5: Storage Integration in Phase 1

**Question**: When data is validated successfully, what happens to it?

**Options Presented**:

- Write to PostgreSQL in Phase 1 ⭐ **SELECTED** (recommended)
- Phase 1 outputs JSON/CSV only
- Staging table (audit trail)

**Follow-up**: Who creates the PostgreSQL schema/tables?

- Phase 1 owns schema creation ⭐ **SELECTED**
- Phase 2 owns schema

**Locked Outcome**:

- Phase 1 writes validated data directly to PostgreSQL
- Phase 1 responsible for creating schema (tables, indexes, constraints)
- Schema includes: `funds`, `nav_history`, with proper constraints

---

### Gray Area 6: Testing & Fixtures

**Question**: What test coverage for Phase 1?

**Options Presented**:

- Unit tests only
- Unit + integration (recommended) ⭐ **SELECTED**
- Comprehensive (UAT fixtures + edge cases)

**Follow-up**: Which scenarios should fixture files cover?

- Valid complete data ⭐ **SELECTED**
- Partial data ⭐ **SELECTED**
- Duplicates ⭐ **SELECTED**
- Malformed rows (not selected)
- Edge cases/empty/wrong format (not selected)

**Locked Outcome**: Unit + integration tests with 3 fixture files (valid complete, partial, duplicates)

---

## Key Trade-offs Resolved

| Trade-off      | Alternative 1      | Alternative 2          | Alternative 3               | Decision                            |
| -------------- | ------------------ | ---------------------- | --------------------------- | ----------------------------------- |
| **Validation** | Strict rejection   | **Partial acceptance** | Transformative              | Partial — resilience + transparency |
| **Schema**     | Minimal (4 fields) | Recommended (6 fields) | **Flexible + configurable** | Configurable + extensible           |
| **Upload**     | Direct (sync)      | **Staging (async)**    | Streaming                   | Async staging — scales better       |
| **Storage**    | **Phase 1 writes** | Phase 2 owns           | Hybrid staging              | Phase 1 writes — self-contained     |

---

## Requirements Coverage Verified

- ✅ REQ-001: CSV file acceptance → Pandas parser + validation
- ✅ REQ-002: Excel file acceptance → Pandas/openpyxl + validation
- ✅ REQ-003: Normalize formats → Configurable schema mapping
- ✅ REQ-004: Validate data quality → Partial acceptance + error report + duplicate detection
- ✅ REQ-005: Web interface upload → Async endpoint + status polling

---

## Next Steps

→ Run `/gsd-plan-phase 1` to create detailed PLAN.md  
→ Researcher will study async job frameworks, Pandas patterns, Pydantic schema design  
→ Planner will estimate tasks, identify risks, create execution timeline

---

_Discussion completed in **--analyze** mode with trade-off tables before each decision._
