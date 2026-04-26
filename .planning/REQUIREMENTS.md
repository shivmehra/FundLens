# FundLens Requirements — v1 MVP

## v1 Requirements (MVP Scope)

### Authentication & Data Ingestion (Phase 1)

- [ ] **REQ-001**: System accepts CSV files with fund data (name, NAV, returns)
- [ ] **REQ-002**: System accepts Excel files (.xlsx format)
- [ ] **REQ-003**: System normalizes diverse formats into unified schema
- [ ] **REQ-004**: System validates data quality before storage (nulls, duplicates)
- [ ] **REQ-005**: User can upload files through web interface

### Storage & Database Setup (Phase 2)

- [ ] **REQ-006**: PostgreSQL stores fund data with queryable schema (name, category, NAV history, KPIs)
- [ ] **REQ-007**: FAISS stores embeddings of textual content for semantic search
- [ ] **REQ-008**: Database supports up to 1000+ funds with complete history

### Retrieval & Context Assembly (Phase 2-3)

- [ ] **REQ-009**: Retrieval layer queries PostgreSQL for structured metrics
- [ ] **REQ-010**: Retrieval layer queries FAISS for relevant text (semantic search)
- [ ] **REQ-011**: Results from both stores combined for context assembly

### LLM Generation & Response (Phase 3)

- [ ] **REQ-012**: Local LLM receives query + structured data + text chunks as context
- [ ] **REQ-013**: LLM generates natural language response with numbers and reasoning
- [ ] **REQ-014**: Generation layer routes to appropriate LLM (Llama/HuggingFace)

### Visualization (Phase 4)

- [ ] **REQ-015**: System generates charts dynamically (NAV trends, returns comparison)
- [ ] **REQ-016**: System generates comparison charts (multiple funds side-by-side)
- [ ] **REQ-017**: Charts rendered with Matplotlib/Plotly

### Chatbot Interface (Phase 4-5)

- [ ] **REQ-018**: User can ask questions in natural language
- [ ] **REQ-019**: User receives text + charts in single response
- [ ] **REQ-020**: User can export insights as PDF

## v2 Requirements (Future Phases)

### Document Support

- PDF files containing fund reports
- Word documents (.docx)
- Notepad text files
- Power BI exports

### Advanced Features

- Multi-fund comparison queries
- Time-range analysis ("2024 vs 2025")
- Follow-up question suggestions
- Chat history across conversations

### UI Enhancements

- PowerPoint export functionality
- Advanced filtering (date range, fund category)
- Save favorite queries
- User preferences/themes

## Out of Scope

- **Real-time market data feeds** — File-based ingestion only
- **Automated trading recommendations** — Analysis only, no advisory
- **Multi-user accounts** — Single-user MVP
- **Cloud deployment** — Local execution only
- **API authentication layer** — Not required for MVP
- **Mobile app** — Web interface only in MVP

## Traceability to Roadmap

| Phase                         | Requirements                     |
| ----------------------------- | -------------------------------- |
| Phase 1: Data Pipeline        | REQ-001, 002, 003, 004, 005      |
| Phase 2: Storage & Retrieval  | REQ-006, 007, 008, 009, 010, 011 |
| Phase 3: LLM Integration      | REQ-012, 013, 014                |
| Phase 4: Visualization & UI   | REQ-015, 016, 017, 018, 019, 020 |
| Phase 5: Testing & Deployment | All v1 requirements validated    |

---

_Last updated: 2026-04-26_
