# Technical Architecture & System Design

## 1. CLI Orchestrator (`cli.py`)
LawNidhi is driven by a central CLI orchestrator. It acts as the routing layer, parsing user arguments and delegating them to the appropriate subsystem (scraper, parser, or database).
- **Workflows:** Include `sync-cause-lists`, `search-case`, and `download-case-orders`.

## 2. Scraping & Parsing Layer
- **`lawnidhi.scraper/`**: Manages HTTP interactions with the NGT website. It handles dynamic case search, cause list fetching, and CAPTCHA solving.
- **`lawnidhi.parsers/`**: Utilizes `pdfplumber` to ingest unstructured PDF orders and schedules. It converts tabular legal data into structured Pydantic models.

## 3. Persistence Layer (`lawnidhi.db/`)
- Utilizes a local SQLite database (`lawnidhi.db`) for lightweight, portable persistence.
- Implements a strict Repository pattern to isolate SQL queries from the application logic.

## 4. RAG Roadmap (Pending Implementation)
As detailed in the Backlog, the RAG architecture is evolving:
- **Phase 1 (Done):** Dynamic Top-K and Similarity thresholds for context windowing.
- **Phase 2 (Active):** Hybrid Search (BM25 + Vector) parity with NotebookLM.
- **Phase 3 (Pending):** Cross-Encoder reranking for secondary Top-K scoring to improve accuracy on legal citations.
