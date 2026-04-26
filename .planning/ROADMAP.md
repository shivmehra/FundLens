# FundLens Roadmap — MVP (5 Phases)

## Roadmap Overview

| Phase | Name                               | Goal                                              | Requirements                     | Status   |
| ----- | ---------------------------------- | ------------------------------------------------- | -------------------------------- | -------- |
| 1     | Data Ingestion Pipeline            | Accept and normalize diverse fund data formats    | REQ-001, 002, 003, 004, 005      | Planning |
| 2     | Storage & Retrieval Infrastructure | Set up databases and enable dual-mode retrieval   | REQ-006, 007, 008, 009, 010, 011 | Pending  |
| 3     | LLM Generation & Orchestration     | Integrate LLM for intelligent response generation | REQ-012, 013, 014                | Pending  |
| 4     | Visualization & Chat Interface     | Render charts and build user-facing chatbot       | REQ-015, 016, 017, 018, 019, 020 | Pending  |
| 5     | Testing, Optimization & Release    | Validate quality, optimize performance, deploy    | All v1 validated                 | Pending  |

**Coverage:** All 20 v1 requirements mapped to exactly one phase ✓

---

## Phase Details

### Phase 1: Data Ingestion Pipeline

**Goal:** Build robust system to accept, validate, and normalize fund data from multiple file formats

**Requirements:**

- REQ-001: System accepts CSV files with fund data (name, NAV, returns)
- REQ-002: System accepts Excel files (.xlsx format)
- REQ-003: System normalizes diverse formats into unified schema
- REQ-004: System validates data quality before storage (nulls, duplicates)
- REQ-005: User can upload files through web interface

**Success Criteria:**

1. CSV/Excel files uploaded and parsed without errors
2. Data normalized to standard schema (fund name, NAV, returns, category)
3. Invalid rows logged and skipped; valid rows stored
4. API endpoints accept multipart file uploads
5. Validation returns clear error messages for malformed data

**Dependencies:** None (foundation)

**Complexity:** Medium

- File parsing libraries (pandas, openpyxl) well-established
- Data normalization straightforward with schema definition
- Validation logic is deterministic

**Tech Stack References:**

- Pandas for CSV/Excel parsing
- FastAPI endpoints for file uploads
- Pydantic for schema validation

---

### Phase 2: Storage & Retrieval Infrastructure

**Goal:** Set up PostgreSQL and FAISS databases, establish retrieval patterns for both structured and semantic queries

**Requirements:**

- REQ-006: PostgreSQL stores fund data with queryable schema
- REQ-007: FAISS stores embeddings of textual content
- REQ-008: Database supports up to 1000+ funds with complete history
- REQ-009: Retrieval layer queries PostgreSQL for structured metrics
- REQ-010: Retrieval layer queries FAISS for relevant text (semantic search)
- REQ-011: Results from both stores combined for context assembly

**Success Criteria:**

1. PostgreSQL schema created with fund, nav_history, performance_metrics tables
2. FAISS index initialized and searchable (10k+ document vectors)
3. Retrieval queries return structured + semantic results in <500ms
4. Context assembly combines both retrieval types correctly
5. Database supports 1000+ funds without performance degradation

**Dependencies:**

- Phase 1 (data ingestion) must complete first to populate databases

**Complexity:** Medium-High

- PostgreSQL schema design requires normalization
- FAISS integration and embedding strategy critical for performance
- Retrieval orchestration must balance accuracy with latency

**Tech Stack References:**

- PostgreSQL with psycopg2 driver
- FAISS for semantic search
- Sentence-transformers for embeddings (e.g., MiniLM)

---

### Phase 3: LLM Generation & Orchestration

**Goal:** Integrate local LLM to generate intelligent responses combining structured data + semantic context

**Requirements:**

- REQ-012: Local LLM receives query + structured data + text chunks as context
- REQ-013: LLM generates natural language response with numbers and reasoning
- REQ-014: Generation layer routes to appropriate LLM (Llama/HuggingFace)

**Success Criteria:**

1. LLM model loaded and callable locally (<500MB memory footprint ideal)
2. Prompts constructed with context (data + text + structured metrics)
3. Generated responses include numbers, reasoning, and citations
4. Response generation completes in <10 seconds for typical query
5. Fallback handling for malformed or no-context scenarios

**Dependencies:**

- Phase 2 (retrieval) must provide structured + semantic context

**Complexity:** High

- Prompt engineering critical for reasoning quality
- Context window management (fitting data + query + response)
- LLM selection (Llama 2/Mistral balance quality vs resource use)

**Tech Stack References:**

- Llama 2 or Mistral 7B (open-source, low resource)
- LangChain or direct transformers for orchestration
- Prompt templates for consistent formatting

---

### Phase 4: Visualization & Chat Interface

**Goal:** Build user-facing chatbot with dynamic visualizations and natural language responses

**Requirements:**

- REQ-015: System generates charts dynamically (NAV trends, returns comparison)
- REQ-016: System generates comparison charts (multiple funds side-by-side)
- REQ-017: Charts rendered with Matplotlib/Plotly
- REQ-018: User can ask questions in natural language
- REQ-019: User receives text + charts in single response
- REQ-020: User can export insights as PDF

**Success Criteria:**

1. User submits query via web form or chat interface
2. System returns text response + relevant chart (if applicable)
3. Charts render correctly for NAV trends, returns, category distribution
4. Multi-fund comparison generates side-by-side charts
5. PDF export includes text + charts with proper formatting

**Dependencies:**

- Phase 3 (LLM generation) must produce text responses
- Phase 2 (retrieval) must provide chart-ready data

**Complexity:** Medium

- Chart generation with Plotly/Matplotlib straightforward
- UI framework (React or Python framework) integrates components
- PDF export libraries (reportlab, weasyprint) handle formatting

**Tech Stack References:**

- React for frontend (or Streamlit for rapid prototyping)
- Plotly for interactive charts
- ReportLab or WeasyPrint for PDF export

---

### Phase 5: Testing, Optimization & Release

**Goal:** Validate all requirements, optimize performance, prepare for production deployment

**Requirements:**

- All v1 requirements validated through UAT

**Success Criteria:**

1. Unit tests cover all core modules (>80% coverage)
2. Integration tests validate end-to-end flows (file upload → response)
3. Performance testing ensures <2s response time for 95th percentile queries
4. Manual UAT confirms all 20 requirements working as intended
5. Documentation complete (setup, usage, architecture)
6. Release artifacts packaged (Docker, requirements.txt, README)

**Dependencies:**

- All phases 1-4 must be complete and functional

**Complexity:** Medium

- Test writing straightforward once features are complete
- Performance optimization may require profiling and tuning
- Documentation and packaging are process-oriented

---

## Key Architecture Insights

**Build Order Rationale:**

1. **Phase 1 → Phase 2**: Can't test storage without data
2. **Phase 2 → Phase 3**: Can't generate answers without retrieval
3. **Phase 3 → Phase 4**: Can't build UI without core logic
4. **Phase 4 → Phase 5**: Testing happens after features complete

**Hybrid Retrieval Pattern:**

- Structured queries (SQL) for exact numeric lookups
- Semantic queries (FAISS) for commentary and explanation
- Both necessary for high-quality responses

**Performance Assumptions:**

- Retrieval: <500ms (combined SQL + FAISS)
- LLM Generation: <10 seconds (including model load on first call)
- Total response: <15 seconds end-to-end

---

## Risk & Mitigation

| Risk                             | Mitigation                                                | Phase   |
| -------------------------------- | --------------------------------------------------------- | ------- |
| LLM response quality inadequate  | Prompt engineering + test against examples early          | Phase 3 |
| Data normalization edge cases    | Build validation exhaustively; test with real fund data   | Phase 1 |
| FAISS index performance at scale | Benchmark with 10k+ vectors; profile retrieval latency    | Phase 2 |
| UI/UX poor user adoption         | User testing with stakeholders; iterate based on feedback | Phase 4 |

---

_Last updated: 2026-04-26_
