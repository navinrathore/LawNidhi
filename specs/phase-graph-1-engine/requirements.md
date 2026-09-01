# Phase 1 Requirements: Legal Ontology & Embedded Graph Engine (Kùzu)

## Objective
Establish the core Knowledge Graph data layer for LawNidhi by defining typed Pydantic ontology schemas and building an embedded, zero-server Graph Store using [`Kùzu`](https://kuzudb.com).

## Background & Problem
LawNidhi currently stores legal hearing schedules and basic case metadata in an SQLite relational database (`lawnidhi.db`). While relational tables excel at 1D lookups (e.g. `SELECT * FROM cases WHERE status = 'OPEN'`), they cannot easily represent or traverse multi-hop legal relationship webs:
- Which precedents are cited across different benches?
- Which counsels frequently appear for specific respondent authorities?
- How are statutory provisions (e.g. NGT Act Section 14/15) linked to specific penalty orders?

## Requirements

### 1. Domain Ontology Schemas (`schema.py`)
- Define strongly typed Pydantic models for legal entities:
  - `LegalEntity`: Base entity with `id`, `name`, `entity_type` (e.g. `CASE`, `JUDGE`, `BENCH`, `COUNSEL`, `PARTY`, `STATUTE`, `ORDER`, `DIRECTION`), and optional `properties` dictionary.
  - `LegalRelation`: Relation linking `source_id` to `target_id` with `relation_type` (e.g. `HEARD_AT`, `PRESIDED_BY`, `REPRESENTS`, `PARTY_TO`, `INVOKES_STATUTE`, `CITES_PRECEDENT`, `ISSUED_DIRECTION`) and `weight`.
  - `GraphExtraction`: Container model holding lists of `LegalEntity` and `LegalRelation` instances.

### 2. Embedded Graph Store Engine (`store.py`)
- Implement `LegalGraphStore` backed by `kuzu.Database` with:
  - Automatic directory management for the database files (default: `data/lawnidhi_graph/`).
  - Idempotent schema initialization creating `LegalEntity` Node Table and `RelatesTo` Rel Table.
  - CRUD operations: `insert_entity`, `insert_relation`, `insert_graph_data` (batch insert).
  - Graph traversal queries:
    - `get_entity(entity_id)`: Retrieve node details and properties.
    - `get_neighbors(entity_id, relation_type=None, direction='BOTH')`: Fetch 1-hop connected nodes.
    - `find_connected_precedents(case_id)`: 2-hop traversal finding all cited precedents and invoked statutes.
    - `get_graph_stats()`: Return total node counts, edge counts, and entity type distributions.
  - Safe connection cleanup and context manager support (`with LegalGraphStore(...) as store:`).

### 3. Unit Test Suite (`tests/test_graph_store.py`)
- Test initialization, idempotency, node insertion, edge creation, multi-hop Cypher queries, and graph stats calculation in a temporary test directory.
