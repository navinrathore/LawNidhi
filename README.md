# LawNidhi

LawNidhi is a robust Python-based CLI tool designed to manage a legal case portfolio. It specifically includes tools for scraping NGT (National Green Tribunal) cause lists, downloading order PDFs, and storing case metadata locally in an SQLite database.

## Project Architecture & Components

The project is structured into the following core components:

- **`cli.py`**: The primary entry point. It orchestrates all CLI commands, parsing arguments, and routing them to the correct internal handlers.
- **`lawnidhi.scraper/`**: Contains logic to interact with the NGT website, including CAPTCHA solving, dynamic case search, and fetching cause list schedules.
- **`lawnidhi.parsers/`**: Specialized modules (using tools like `pdfplumber`) to parse unstructured NGT PDF schedules and extract tabular legal data.
- **`lawnidhi.graph/`**: Embedded Property Graph engine backed by Kùzu. Provides high-performance Cypher querying for legal entities, judicial relationships, and precedent clustering.
- **`lawnidhi.rag/`**: Hybrid GraphRAG retrieval engine. Combines semantic vector text search (via scikit-learn TF-IDF) with multi-hop Knowledge Graph expansion for deeply grounded legal intelligence.
- **`lawnidhi.server/`**: FastAPI REST bridge that exposes the Knowledge Graph and RAG retriever to external dashboards, microservices, and Open-NotebookLM.
- **`lawnidhi.db/`**: Handles local SQLite persistence (`lawnidhi.db`). It contains the schema definition, ingestion logic, and repository patterns for executing queries safely.
- **`lawnidhi.models/`**: Pydantic models that define the strict shapes of cases, schedules, and parties.
- **`lawnidhi.app/`**: Core application logic for generating reports (like counsel appearance logs) and running database queries.

## Getting Started & Execution

To run LawNidhi, ensure you have activated your virtual environment and installed the dependencies:

```bash
# Activate the virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### Primary Commands

The tool is executed via `cli.py`. Below are the primary commands grouped by workflow:

#### FastAPI REST Server (Graph RAG Bridge)
- **`python cli.py serve --host 127.0.0.1 --port 8000`**: Start the Uvicorn REST server. Exposes the Knowledge Graph, RAG endpoints, and Swagger UI at `http://localhost:8000/docs`.

#### Core Pipeline (Scraping & Parsing)
- **`python cli.py sync-cause-lists`**: Scan the NGT site and update the local database with new hearing schedules.
- **`python cli.py search-case 83/2025`**: Search for a specific case by its number and year to find its Diary Number.
- **`python cli.py download-case-orders 83/2025`**: Execute the full pipeline to search the case, solve the CAPTCHA, and download all available order PDFs.

#### Portfolio Management
- **`python cli.py add-case 83/2025 --title "Example Case"`**: Add a case to your managed portfolio.
- **`python cli.py list-cases`**: Browse all cases currently in your portfolio.
- **`python cli.py update-case 83/2025 --status OPEN`**: Update the status or details of a tracked case.

#### Reports & Exploration
- **`python cli.py generate-invoice`**: Create an appearance log report for billing.
- **`python cli.py db-stats`**: View the current health and row counts of your local database.

---
*Note: LawNidhi strictly adheres to Spec-Driven Development (SDD). The project features a hybrid deterministic RAG engine designed specifically for the Agentic Co-Counsel architecture (following a $0 token tax methodology).*
