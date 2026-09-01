# Phase 5 Plan: Hybrid GraphRAG Retriever

## Implementation Steps

### Step 1: Data Structures & Schemas (`lawnidhi/rag/schema.py`)
- Define Pydantic models:
  - `TextChunk`: text, chunk_id, doc_id, case_name, order_date, score.
  - `GraphContextNode`: id, name, type, relation.
  - `HybridRetrievalResult`: query, text_chunks, graph_nodes, statutory_provisions, precedent_lineage, formatted_context.
  - `RAGAnswer`: query, answer, source_cases, cited_statutes, cited_precedents.

### Step 2: Vector Document Store (`lawnidhi/rag/vector_store.py`)
- Implement `LegalDocumentStore`:
  - Scans and indexes order PDF texts in `data/orders/`.
  - Splits text into semantic chunks (~500 chars with 100 char overlap).
  - Builds TF-IDF + Cosine similarity retrieval matrix (with pluggable dense vector search interface).

### Step 3: Graph Context Expander (`lawnidhi/rag/graph_expander.py`)
- Implement `GraphContextExpander`:
  - Resolves Case nodes in Kùzu DB from vector search results or explicit query tokens.
  - Traverses `INVOKES_STATUTE`, `CITES_PRECEDENT`, and `DELIVERED_BY` relationships.
  - Formats clean deduplicated statutory and precedent lists.

### Step 4: Hybrid Retriever Engine (`lawnidhi/rag/hybrid_retriever.py`)
- Implement `HybridGraphRAGRetriever`:
  - Executes parallel vector search + graph traversal.
  - Applies Reciprocal Rank Fusion (RRF).
  - Synthesizes formatted, LLM-ready context with zero hallucination.

### Step 5: Provider-Agnostic Synthesis Wrapper (`lawnidhi/rag/synthesizer.py`)
- Implement `LegalSynthesizer`:
  - Structured extraction fallback (deterministic summary generator when offline or no API key).
  - Pluggable LLM completion interface following Workspace Rule 2 & Rule 11.

### Step 6: REST API & CLI Registration
- Add `lawnidhi/server/routes/rag.py` with `POST /api/rag/retrieve` and `POST /api/rag/ask`.
- Register `rag_router` in `lawnidhi/server/app.py`.
- Add `graph-rag` subcommand in `cli.py`.

### Step 7: Test Suite (`tests/test_hybrid_rag.py`)
- Unit tests for chunking, vector indexing, graph context expansion, hybrid fusion, and API endpoints.
