# Phase 4 Requirements: FastAPI Graph Bridge & REST Service Layer

## Objective
Expose the embedded LawNidhi Kùzu Knowledge Graph and order extraction capabilities as a high-performance, asynchronous REST API service built with FastAPI, enabling frontend visualization, microservices, and Open-NotebookLM GraphRAG backend integration.

## Background & Problem
Prior to Phase 4, the LawNidhi Knowledge Graph is only accessible via CLI commands or direct Python SDK imports. To support:
1. Web Dashboards & Cytoscape.js force-directed graph visualizers.
2. External legal tech microservices and client portals.
3. Open-NotebookLM hybrid vector+graph RAG retriever queries.

We require a decoupled, production-ready HTTP REST API layer with automated OpenAPI documentation, CORS support, connection pooling, and schema validation.

## Architectural Principles (Rules & Guidelines)
- **Zero-Latency In-Memory Graph Access**: Maintain a shared, thread-safe `LegalGraphStore` instance per server process using FastAPI lifespan events.
- **Pydantic Structural Enforcement**: All request payloads and response bodies must use strongly typed Pydantic models.
- **Provider & Client Agnosticism**: Standard JSON API outputs compatible with web browsers, curl, Python SDKs, and mobile clients.

## Functional Requirements

### 1. REST Endpoints Architecture

#### 🏛️ Knowledge Graph Endpoints (`/api/graph`)
- `GET /api/graph/stats`: Total node count, relationship count, entity breakdown.
- `GET /api/graph/daily-board?date=YYYY-MM-DD&court=1`: Courtroom cause list board.
- `GET /api/graph/counsel/{name}/cases?start=YYYY-MM-DD&end=YYYY-MM-DD`: Date-specific appearances for an advocate.
- `GET /api/graph/counsel/{name}/clashes?date=YYYY-MM-DD`: Courtroom clash detection.
- `GET /api/graph/counsel/{name}/portfolio`: Lifetime representation portfolio, judges appeared before, parties represented.
- `GET /api/graph/judge/{name}/caseload`: Judge bench caseload and hearing sessions.
- `GET /api/graph/case/{case_id}/timeline`: Chronological listing timeline with interval gaps.
- `GET /api/graph/case/{case_id}/precedents`: Multi-hop precedent citations and statutory sections.
- `POST /api/graph/query`: Raw openCypher query executor (`{"query": "MATCH (n) RETURN n"}`).
- `GET /api/graph/export?format=json|dot|gexf`: Full graph topology export.

#### 📄 Order Extraction Endpoints (`/api/orders`)
- `POST /api/orders/extract`: Parse an uploaded PDF and return structured triplets with optional immediate graph ingestion.
- `POST /api/orders/sync`: Trigger batch ingestion of order PDFs directory.

### 2. Service Management (`cli.py serve`)
- CLI command to start Uvicorn dev/production server:
  `python projects/LawNidhi/cli.py serve --host 127.0.0.1 --port 8000 [--reload]`

### 3. Automated Documentation
- Interactive Swagger UI at `http://localhost:8000/docs`.
- ReDoc interactive documentation at `http://localhost:8000/redoc`.
