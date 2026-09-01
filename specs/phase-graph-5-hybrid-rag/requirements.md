# Phase 5 Requirements: Hybrid GraphRAG Retriever (Vector + Kùzu Graph Expansion)

## Objective
Implement a high-precision, citation-grounded Hybrid GraphRAG (Retrieval-Augmented Generation) engine that combines dense/sparse semantic text retrieval of judicial order PDFs with multi-hop Knowledge Graph traversal (statutory sections, precedent citations, coram judges) for Open-NotebookLM legal intelligence.

## Problem Statement & Motivation
Standard vector-only RAG has critical failure modes in legal research:
1. **The Precedent Blindspot**: Paragraph embeddings cannot follow citation chains (e.g. *Case A cites Supreme Court Precedent B regarding Section 25 of Water Act 1974*).
2. **Misattribution & Hallucination**: Pure text generation without explicit structured ontological relationships fails to ground statutory penalties to the exact legal section.
3. **High Token Tax**: Relying on frontier LLMs to repeatedly reconstruct relationships across long PDFs wastes money and introduces latency.

## Architecture & Design Principles
- **Deterministic Core Layer (Rule 11 - Hybrid Supervisory Wrapper Pattern)**: The hybrid retrieval, graph traversal, and context assembly must be 100% deterministic, standalone, and fast with $0$ LLM token overhead.
- **Provider-Agnostic Interface (Rule 2)**: Any generative synthesis layer must operate behind unified interfaces, capable of running local SLMs (via vLLM/llama.cpp) or cloud providers.
- **Multi-Hop Subgraph Expansion**: For every retrieved case document, expand its 1-to-2 hop neighborhood in Kùzu DB (`INVOKES_STATUTE`, `CITES_PRECEDENT`, `DELIVERED_BY`, `REPRESENTS`).
- **Reciprocal Rank Fusion (RRF)**: Blend lexical text match and vector similarity scores with graph centrality.

## Functional Requirements

### 1. Document Indexer (`lawnidhi/rag/vector_store.py`)
- Ingest and chunk text from judicial order PDFs in `data/orders/`.
- Maintain document metadata (Case ID, Date, Bench, File Path).
- Provide TF-IDF / Cosine semantic search with an extensible dense embedding abstraction.

### 2. Graph Subgraph Expander (`lawnidhi/rag/graph_expander.py`)
- Given candidate Case IDs or keywords, extract 1-to-2 hop subgraphs from Kùzu DB.
- Aggregate all connected `SECTION` (invoked acts & rules), `CASE` (precedents), and `JUDGE` (bench) nodes into structured Pydantic models.

### 3. Hybrid Retriever & Context Assembler (`lawnidhi/rag/hybrid_retriever.py`)
- Combine textual chunks with graph triplets into a structured `HybridRetrievalResult`.
- Format a Markdown-grounded context payload with explicit legal citation headers.

### 4. REST API & CLI Integration
- REST API:
  - `POST /api/rag/retrieve`: Retrieve hybrid text + graph context.
  - `POST /api/rag/ask`: Generate structured legal answer with citations.
- CLI:
  - `python projects/LawNidhi/cli.py graph-rag "<query>" [--top-k 5] [--synthesize]`
