# Phase 1 Technical Plan: Legal Ontology & Embedded Graph Engine

## Component Architecture

```
projects/LawNidhi/lawnidhi/graph/
├── __init__.py          # Export LegalEntity, LegalRelation, GraphExtraction, LegalGraphStore
├── schema.py            # Pydantic models for nodes, relations, and extraction containers
└── store.py             # Kùzu database engine wrapper and Cypher query execution
```

## Detailed Implementation Steps

### Step 1: `lawnidhi/graph/schema.py`
1. Define `EntityType` Literal / Enum (`CASE`, `JUDGE`, `BENCH`, `COUNSEL`, `PARTY`, `STATUTE`, `ORDER`, `DIRECTION`).
2. Define `RelationType` Literal / Enum (`HEARD_AT`, `PRESIDED_BY`, `REPRESENTS`, `PARTY_TO`, `INVOKES_STATUTE`, `CITES_PRECEDENT`, `ISSUED_DIRECTION`, `CONTAINS_ORDER`).
3. Define `LegalEntity(BaseModel)` with normalization helper:
   - `id`: Unique string (lowercase slug, e.g. `case_oa_83_2025`).
   - `name`: Display string (e.g. `OA 83/2025`).
   - `entity_type`: Category string.
   - `properties`: Dict of arbitrary metadata.
4. Define `LegalRelation(BaseModel)` with `source_id`, `relation_type`, `target_id`, `weight`, `properties`.
5. Define `GraphExtraction(BaseModel)` containing `entities: List[LegalEntity]` and `relationships: List[LegalRelation]`.

### Step 2: `lawnidhi/graph/store.py`
1. Implement `LegalGraphStore`:
   - Accept `db_path: str = "data/lawnidhi_graph"`.
   - Initialize `kuzu.Database(db_path)` and `kuzu.Connection(db)`.
   - Run `CREATE NODE TABLE IF NOT EXISTS LegalEntity (id STRING, name STRING, entity_type STRING, properties STRING, PRIMARY KEY (id))`
   - Run `CREATE REL TABLE IF NOT EXISTS RelatesTo (FROM LegalEntity TO LegalEntity, relation_type STRING, weight DOUBLE, properties STRING)`
2. Add Cypher query methods:
   - `insert_entity(entity: LegalEntity)`
   - `insert_relation(relation: LegalRelation)`
   - `insert_graph_data(data: GraphExtraction)`
   - `get_entity(entity_id: str) -> Optional[dict]`
   - `get_neighbors(entity_id: str, relation_type: Optional[str] = None) -> List[dict]`
   - `find_connected_precedents(case_id: str) -> List[dict]`
   - `get_graph_stats() -> dict`
   - `close()` and `__enter__` / `__exit__` context management.

### Step 3: `lawnidhi/graph/__init__.py`
Export public APIs for clean imports across LawNidhi and Open-NotebookLM.

### Step 4: Unit Testing (`tests/test_graph_store.py`)
Write comprehensive tests using `tmp_path` pytest fixture to verify:
1. Store instantiation and schema creation.
2. Entity and relationship insertion (including idempotency).
3. 1-hop neighbor lookup.
4. 2-hop precedent and statute traversal.
5. Graph summary statistics calculation.
