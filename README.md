# ⚖️ NyayaGraph (न्यायGraph)

**NyayaGraph** is an enterprise-grade Autonomous Litigation Intelligence & Legal Knowledge Graph platform for Indian tribunals and courts (starting with the National Green Tribunal / NGT, expanding to High Courts and the Supreme Court of India).

It features **VidhiGraph** (विधिGraph) as its dedicated statutory sub-graph, providing structured, timeless knowledge of codified central and state acts, rules, and statutory sections.

---

## 🏛️ System Architecture

```
                                  NyayaGraph Platform
                         (Master Litigation Intelligence)
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
    ┌─────────────────┐                                   ┌─────────────────┐
    │   VidhiGraph    │                                   │ Litigation Core │
    │ (Statutory Sub) │◄─────────[:INVOKES_SECTION]───────┤  & Coram Graph  │
    ├─────────────────┤                                   ├─────────────────┤
    │ • Acts & Codes  │                                   │ • Cause Lists   │
    │ • Sections      │◄─────────[:ALLEGES_VIOLATION]─────┤ • Orders (PDF)  │
    │ • Rules & Sch.  │                                   │ • Bench (Coram) │
    │ • Definitions   │                                   │ • Precedents    │
    └─────────────────┘                                   └─────────────────┘
```

The system is structured into modular components:

- **`cli.py`**: The unified CLI orchestrator (`prog="nyayagraph"`).
- **`nyayagraph.graph/`**: Embedded Property Graph engine backed by Kùzu. Models entities (`Case`, `Judge`, `Counsel`, `Party`, `Section`, `Precedent`) and relationships with openCypher querying. Includes the **VidhiGraph** statutory sub-engine.
- **`nyayagraph.rag/`**: Hybrid GraphRAG retrieval engine. Combines vector text search with multi-hop Knowledge Graph traversals for grounded, hallucination-resistant legal briefs with zero token tax on deterministic summarization (Rule 11).
- **`nyayagraph.agent/`**: Autonomous ReAct Legal Co-Counsel with bounded loops (`max_loops <= 12`) for case brief generation and research.
- **`nyayagraph.scraper/`**: Resilient scraping suite for court portals (cause lists, case search, CAPTCHA solving, and order PDF downloading).
- **`nyayagraph.parsers/`**: PDF parsers using `pdfplumber` to extract tabular cause lists, coram benches, statutory citations, and action items.
- **`nyayagraph.server/`**: FastAPI REST bridge that exposes the Knowledge Graph and RAG retriever to external dashboards, microservices, and Open-NotebookLM.
- **`nyayagraph.db/`**: Local SQLite persistence (`nyayagraph.db`) managing case portfolios, schedules, and appearances.
- **`nyayagraph.models/`**: Strict Pydantic models enforcing schema boundaries across all subsystems.

---

## 🚀 Getting Started & Execution

Ensure dependencies are installed:

```bash
# Install package dependencies
pip install -r requirements.txt
```

### Primary Commands

NyayaGraph is operated via `cli.py`:

#### 1. Knowledge Graph & Analytics
- **`python cli.py graph-stats`**: View total nodes, relationships, and entity breakdown across the graph.
- **`python cli.py graph-sync`**: Ingest all downloaded cause lists into the Knowledge Graph.
- **`python cli.py graph-sync-orders`**: Batch extract and ingest all order PDFs into the Knowledge Graph.
- **`python cli.py graph-timeline 83/2025`**: View chronological hearing timeline for a specific case.
- **`python cli.py graph-daily-board`**: View courtroom cause list board for today/tomorrow.
- **`python cli.py graph-counsel-clashes "Hemlata Singh"`**: Detect multi-courtroom appearance clashes across benches.
- **`python cli.py graph-communities`**: Detect and display macro-thematic legal graph clusters.

#### 2. Hybrid GraphRAG & Agentic Co-Counsel
- **`python cli.py graph-rag "water pollution tanneries Kanpur"`**: Execute Hybrid GraphRAG retrieval (sparse vector search + multi-hop graph expansion).
- **`python cli.py ask "Prepare a case brief for OA 985/2019"`**: Launch the autonomous ReAct Co-Counsel loop.

#### 3. FastAPI REST Service Layer
- **`python cli.py serve --host 127.0.0.1 --port 8000`**: Start the Uvicorn REST server. Exposes the Knowledge Graph, RAG endpoints, and Swagger UI at `http://localhost:8000/docs`.

#### 4. Scraping & Docketing Pipeline
- **`python cli.py sync-cause-lists`**: Scan court portal and update local database with new hearing schedules.
- **`python cli.py search-case 83/2025`**: Search for a case by number and year to resolve Diary Number.
- **`python cli.py download-case-orders 83/2025`**: Full pipeline: search case -> solve CAPTCHA -> download order PDFs.

#### 5. Portfolio Management & Billing
- **`python cli.py add-case 83/2025 --title "Example Case"`**: Add a case to your managed portfolio.
- **`python cli.py list-cases`**: Browse tracked cases in your portfolio.
- **`python cli.py generate-invoice`**: Create an appearance log report for billing.
- **`python cli.py db-stats`**: View row counts and health of the local relational database.

---

## 📋 Architectural Invariants & Rules

- **Zero Token Tax (Rule 11)**: Deterministic core logic operates at 100% functionality without requiring external LLM API calls.
- **Hard ReAct Loop Bounds (Rule 1)**: Autonomous agent research strictly enforces `max_loops <= 12`.
- **Spec-Driven Development (SDD)**: All architectural features are designed and tracked in `specs/roadmap.md` and `specs/backlog.md`.
