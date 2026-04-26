# FundLens — AI-Powered Mutual Fund Insights Chatbot

## What This Is

FundLens is a Retrieval-Augmented Generation (RAG) powered chatbot designed to provide actionable insights into mutual fund performance. It ingests diverse financial data sources (CSV, Excel, PDFs, Word, Notepad, and exported Power BI files), stores them in structured and semantic databases, and delivers natural language explanations with dynamic charts.

This project demonstrates end-to-end AI Solutions Engineering: data ingestion, retrieval, orchestration, visualization, and user-facing interaction — all built with open-source tools.

## Core Value

Enable users to ask natural language questions about mutual fund performance and receive both:

- **Structured insights** — Returns, NAV, CAGR, risk metrics with numbers
- **Visual context** — Dynamic charts comparing funds across time periods
- **Narrative explanation** — Why funds performed differently

One query → immediate, intelligent, visual answer.

## Context

### The Problem

Fund investors struggle to synthesize information from multiple sources:

- Scattered performance data (CSVs, Excel exports, PDFs)
- Time-consuming manual analysis
- Limited visualization without programming knowledge
- No natural language interface for complex questions

### Our Approach

Build a unified system that:

1. Normalizes diverse data formats into structured schema
2. Embeds unstructured commentary for semantic search
3. Routes queries to the right data source (PostgreSQL for metrics, FAISS for analysis)
4. Generates clear, visual, narrative responses
5. Exports insights as charts and reports

### Why This Matters

Demonstrates production-grade AI architecture:

- Multi-source data ingestion and normalization
- Hybrid retrieval (structured + semantic)
- LLM orchestration with domain data
- Real-time visualization
- User-facing conversational interface

## Objectives

- ✓ Enable interactive Q&A on mutual fund performance
- ✓ Combine structured metrics (returns, NAV, CAGR) with unstructured text (reports, commentary)
- ✓ Provide visual storytelling through dynamic charts
- ✓ Demonstrate production-grade RAG patterns

## System Architecture

### 1. Data Ingestion Layer

Accepts multiple file formats:

- CSV/Excel
- PDFs
- Word documents
- Notepad
- Power BI .pbix (exported to CSV)

Normalizes into unified schema:

- Fund name, category, inception date
- NAV history (daily/monthly/yearly)
- Performance KPIs (returns, CAGR, Sharpe ratio, max drawdown)
- Fund metadata (manager, strategy, allocation)

### 2. Storage Layer

**PostgreSQL** — stores structured fund data

- Tables: funds, nav_history, performance_metrics, fund_metadata
- Enables SQL queries for precise numeric lookups

**FAISS (Vector DB)** — stores embeddings of textual content

- Fund reports, analyst commentary, strategy explanations
- Enables semantic search ("Why did this fund outperform?")

### 3. Retrieval Layer

User query → converted into embeddings

- FAISS retrieves relevant text (commentary, reports)
- PostgreSQL queried for structured metrics (returns, CAGR, NAV)
- Results combined for LLM context

### 4. Generation Layer

Local LLM combines:

- Retrieved text chunks
- Structured metrics
- Domain context

Produces natural language insights with reasoning and numbers

### 5. Visualization Layer

- Matplotlib/Plotly generate charts dynamically
- NAV trends, category distribution, peer comparison
- Charts rendered alongside text in response

### 6. User Interface

- React/React Native or Python framework for chatbot
- Displays text + charts
- Export functionality (PDF/PPT for stakeholders)

## Requirements

### Validated

(None yet — shipping to validate)

### Active

#### Data Ingestion (Table Stakes)

- [ ] **REQ-001**: System accepts CSV files with fund data (name, NAV, returns)
- [ ] **REQ-002**: System accepts Excel files (.xlsx format)
- [ ] **REQ-003**: System accepts PDF files containing fund reports
- [ ] **REQ-004**: System accepts Word documents (.docx)
- [ ] **REQ-005**: System normalizes diverse formats into unified schema
- [ ] **REQ-006**: System validates data quality before storage (nulls, duplicates)

#### Storage & Retrieval (Table Stakes)

- [ ] **REQ-007**: PostgreSQL stores fund data with queryable schema (name, category, NAV history, KPIs)
- [ ] **REQ-008**: FAISS stores embeddings of textual content for semantic search
- [ ] **REQ-009**: Retrieval layer queries PostgreSQL for structured metrics
- [ ] **REQ-010**: Retrieval layer queries FAISS for relevant text (semantic search)
- [ ] **REQ-011**: Results from both stores combined for context assembly

#### LLM Generation (Table Stakes)

- [ ] **REQ-012**: Local LLM receives query + structured data + text chunks as context
- [ ] **REQ-013**: LLM generates natural language response with numbers and reasoning
- [ ] **REQ-014**: Generation layer routes to appropriate LLM (GPT/Llama/HuggingFace)

#### Visualization (Table Stakes)

- [ ] **REQ-015**: System generates charts dynamically (NAV trends)
- [ ] **REQ-016**: System generates comparison charts (multiple funds)
- [ ] **REQ-017**: Charts included in response alongside text

#### Chatbot Interface (Table Stakes)

- [ ] **REQ-018**: User can ask questions in natural language
- [ ] **REQ-019**: User receives text + charts in single response
- [ ] **REQ-020**: User can export insights as PDF or PowerPoint

#### Advanced Features (Differentiators)

- [ ] **REQ-021**: System suggests follow-up questions based on user query
- [ ] **REQ-022**: System tracks chat history and context across conversations
- [ ] **REQ-023**: System supports multi-fund comparison queries
- [ ] **REQ-024**: System supports time-range analysis ("2024 vs 2025")

### Out of Scope

- Real-time market data feeds (static file-based only)
- Automated trading recommendations
- Multi-user accounts (single-user MVP)
- Cloud deployment (local execution only)
- API authentication layer

## Key Decisions

| Decision                                  | Rationale                                                                    | Status                 |
| ----------------------------------------- | ---------------------------------------------------------------------------- | ---------------------- |
| Hybrid retrieval (SQL + FAISS)            | Structured data requires precise metrics; unstructured needs semantic search | Approved               |
| Local LLM (not API-dependent)             | Demonstrates reproducibility, avoids API costs                               | Approved               |
| PostgreSQL + FAISS (not single vector DB) | Numeric queries require exact matches; semantic search needs vectors         | Approved               |
| File-based ingestion (not live feeds)     | Reduces complexity for MVP; demonstrates pattern end-to-end                  | Approved               |
| React/Python UI (not headless CLI)        | Demonstrates user-facing implementation                                      | Pending Implementation |

## Constraints

### Technical

- Open-source tools only (no proprietary APIs for core functionality)
- No GPU requirement (CPU-compatible LLMs acceptable)
- Python 3.9+, PostgreSQL 12+

### Timeline

- MVP in ~8-12 weeks (phased delivery per roadmap)

### Budget

- Open-source licensing only
- Development cost only (no hosting, no data licensing)

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):

1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---

_Last updated: 2026-04-26 after initialization_
