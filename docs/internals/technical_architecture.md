# Technical Architecture & System Design

## 1. CLI Orchestrator (`cli.py`)
NyayaGraph is driven by a central CLI orchestrator (`prog="nyayagraph"`). It acts as the routing layer, parsing user arguments and delegating them to the appropriate subsystem (scraper, parser, knowledge graph, or database).
- **Workflows:** Include `graph-stats`, `graph-sync`, `graph-rag`, `ask`, `sync-cause-lists`, `search-case`, and `download-case-orders`.

## 2. Scraping & Parsing Layer
- **`nyayagraph.scraper/`**: Manages HTTP interactions with the NGT website. It handles dynamic case search, cause list fetching, and CAPTCHA solving.
- **`nyayagraph.parsers/`**: Utilizes `pdfplumber` to ingest unstructured PDF orders and schedules. It converts tabular legal data into structured Pydantic models.

## 3. Persistence Layer (`nyayagraph.db/`)
- Utilizes a local SQLite database (`nyayagraph.db`) for lightweight, portable persistence.
- Implements a strict Repository pattern to isolate SQL queries from the application logic.

## 4. RAG Roadmap (Pending Implementation)
As detailed in the Backlog, the RAG architecture is evolving:
- **Phase 1 (Done):** Dynamic Top-K and Similarity thresholds for context windowing.
- **Phase 2 (Active):** Hybrid Search (BM25 + Vector) parity with NotebookLM.
- **Phase 3 (Pending):** Cross-Encoder reranking for secondary Top-K scoring to improve accuracy on legal citations.
