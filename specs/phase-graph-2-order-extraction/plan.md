# Phase 2 Plan: PDF Order Triplet Extraction & Precedent Citation Graph

## Implementation Steps

### Step 1: Pydantic Schema Extensions (`lawnidhi/graph/schema.py`)
- Define:
  - `StatuteReference`: `act_name`, `section`, `sub_section`.
  - `PrecedentCitation`: `title`, `citation` (e.g. `(1996) 5 SCC 647`), `court`, `year`.
  - `JudicialDirection`: `direction_text`, `direction_type` (`PENALTY`, `COMMITTEE`, `STAY`, `COMPLIANCE`).
  - `OrderExtractionResult`: Complete structured container for order extraction.

### Step 2: Deterministic Statutory Section Extractor (`lawnidhi/parsers/ngt/statute_parser.py`)
- Implement regex-based extraction for all major environmental acts with normalized names:
  - `"NGT Act, 2010"` $\rightarrow$ `Section 14`, `Section 15`, `Section 19`, `Section 20`.
  - `"Water Act, 1974"` $\rightarrow$ `Section 25`, `Section 33A`.
  - `"Air Act, 1981"` $\rightarrow$ `Section 21`, `Section 31A`.
  - `"Environment (Protection) Act, 1986"` $\rightarrow$ `Section 3`, `Section 5`.
  - Generic pattern matcher: `(?:Section|Sec\.?|Rule)\s+(\d+[A-Za-z]*(?:\(\d+\))?)\s+(?:of\s+(?:the\s+)?)?([A-Za-z\s,\(\)]+Act,?\s*\d{4})`

### Step 3: PDF Order Text Extractor (`lawnidhi/parsers/ngt/order_parser.py`)
- Extract plain text from PDF with page tracking.
- Header parser for Coram/Judges, Case Number, and Hearing/Order Date.
- Extraction runner orchestrating deterministic statutory parsing + optional LLM precedent extraction.

### Step 4: Graph Synchronization Module (`lawnidhi/graph/order_sync.py`)
- Function `ingest_order_extraction(store: LegalGraphStore, extraction: OrderExtractionResult) -> Dict[str, int]`:
  - Upsert `CASE` node (or link to existing).
  - Upsert `STATUTE` and `SECTION` nodes and link `(Case)-[:INVOKES_STATUTE]->(Section)`.
  - Upsert `CASE` node for cited precedent and link `(Case)-[:CITES_PRECEDENT]->(Precedent_Case)`.
  - Upsert `DIRECTION` / `PENALTY` nodes and link `(Case)-[:ISSUED_DIRECTION]->(Direction)`.
  - Upsert `JUDGE` nodes and link `(Case)-[:DELIVERED_BY]->(Judge)`.

### Step 5: CLI Subcommand Integration (`cli.py`)
- Add `graph-extract-order <pdf_path> [--ingest]`
- Add `graph-sync-orders [--dir <orders_dir>]`

### Step 6: Unit Test Suite (`tests/test_order_extraction.py`)
- Test regex statutory pattern matcher across diverse case texts.
- Test PDF order text parser with real sample PDF in `data/orders/`.
- Test graph ingestion and multi-hop precedent/statute retrieval in Kùzu DB.
