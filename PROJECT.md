FundLens – Mutual Fund Insights Chatbot
🔎 Project Summary
FundLens is a Retrieval-Augmented Generation (RAG) powered chatbot designed to provide actionable insights into mutual fund performance. It ingests diverse financial data sources (CSV, Excel, PDFs, Word, Notepad, and exported Power BI files), stores them in structured and semantic databases, and delivers natural language explanations with dynamic charts.

This project demonstrates end-to-end AI Solutions Engineering: data ingestion, retrieval, orchestration, visualization, and user-facing interaction — all built with open-source tools.

A. Objectives
Enable interactive Q&A on mutual fund performance.
Combine structured metrics (returns, NAV, CAGR) with unstructured text (reports, commentary).
Provide visual storytelling through dynamic charts.

B. System Architecture

1. Data Ingestion Layer
   Accepts multiple file formats:

CSV/Excel
PDFs
Word
Notepad
Power BI .pbix → export tables to CSV before ingestion

Normalizes into a unified schema (fund name, category, NAV history, KPIs).

2. Storage Layer
   PostgreSQL → stores structured fund data (tables, KPIs, performance metrics).

FAISS (Vector DB) → stores embeddings of textual content (fund reports, commentary, notes).

3. Retrieval Layer
   User query → converted into embeddings.

FAISS retrieves relevant text (commentary, reports).

PostgreSQL queried for structured metrics (returns, CAGR, NAV).

4. Generation Layer
   Local LLM combines retrieved text + structured metrics.

Produces natural language insights with reasoning and numbers.

5. Visualization Layer
   Matplotlib/Plotly → generate charts dynamically (NAV trends, category distribution).

Charts returned alongside text in chatbot UI.

6. User Interface
   React/React Native or some python framework for Interface chatbot.

Displays text + charts.

Option to export insights into PDF/PPT for stakeholders.

🔄 Pipeline Flow
User Query → “Compare top 3 balanced funds in 2025.”

Embedding + Retrieval → FAISS finds commentary, PostgreSQL fetches metrics.

Context Assembly → NAV history, CAGR, risk scores.

LLM Generation → Insight: “ABC Balanced Fund grew 14% in 2025, outperforming peers by 3% due to diversified allocation.”

Visualization → Plotly chart comparing top 3 funds.

Response → Chatbot shows text + chart.

⚙️ Tech Stack
Data ingestion: Pandas, PyPDF2, python-docx, openpyxl

Database: PostgreSQL (structured), FAISS (semantic)

Backend: FastAPI/Django

LLM: GPT/Llama/HuggingFace model

Visualization: Matplotlib/Plotly

Frontend: React/React Native chatbot or some Python Framework Chatbot

📊 Example Use Cases
“Summarize top 5 equity funds by 3-year CAGR.”

“Explain why balanced funds outperformed peers in 2024.”

“Generate a chart of NAV trends for XYZ Fund.”

“Summarize PDF commentary on sector allocation impact.”
