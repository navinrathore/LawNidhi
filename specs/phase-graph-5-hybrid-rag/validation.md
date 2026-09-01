# Phase 5 Validation Plan: Hybrid GraphRAG Retriever

## Automated Test Coverage (`tests/test_hybrid_rag.py`)

1. **Vector Document Store**:
   - Verify indexing of sample texts and PDF documents.
   - Verify cosine search score ranking on queries (e.g., `"Water pollution effluent discharge"`).
2. **Graph Context Expander**:
   - Verify multi-hop subgraph expansion around case `985/2019` returns `Water Act 1974` and `Vellore Citizens Welfare Forum`.
3. **Hybrid Retriever**:
   - Verify that querying `"Water Act Section 25"` returns both the textual passage AND the linked Knowledge Graph `SECTION` and `PRECEDENT` nodes.
4. **Context Formatter**:
   - Verify that `formatted_context` contains clean Markdown headings ready for prompt ingestion.
5. **REST API Endpoints**:
   - `POST /api/rag/retrieve` returns 200 OK with `text_chunks` and `graph_nodes`.
   - `POST /api/rag/ask` returns 200 OK with `answer` and citation lists.
6. **CLI Command**:
   - `python projects/LawNidhi/cli.py graph-rag "Water Act Section 25"` executes without error and prints structured results.
