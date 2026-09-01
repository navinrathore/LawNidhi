# Phase 2 Validation Plan: PDF Order Triplet Extraction & Precedent Citation Graph

## Automated Unit & Integration Tests

### 1. Statutory Regex Precision Tests (`tests/test_statute_parser.py`)
- Verify extraction of:
  - `"Section 14 of the National Green Tribunal Act, 2010"` $\rightarrow$ `Act: NGT Act 2010`, `Section: 14`
  - `"Section 21 of the Air (Prevention and Control of Pollution) Act, 1981"` $\rightarrow$ `Act: Air Act 1981`, `Section: 21`
  - `"Section 33A of Water Act, 1974"` $\rightarrow$ `Act: Water Act 1974`, `Section: 33A`
  - Multiple compound citations in a single paragraph.

### 2. PDF Order Parsing Test
- Parse a real sample PDF from `projects/LawNidhi/data/orders/070110900591-2019_01-07-2025_order.pdf`.
- Validate that coram judges, case number, and order date are extracted without exceptions.

### 3. Graph Ingestion & Traversal Test
- Ingest the extracted `OrderExtractionResult` into a temporary test `LegalGraphStore`.
- Verify:
  - `(Case)-[:INVOKES_STATUTE]->(Section)` is queryable.
  - `(Case)-[:CITES_PRECEDENT]->(Precedent)` is queryable.
  - `find_connected_precedents()` returns the newly ingested statutory and precedent edges.

## Manual CLI Verification

```bash
# 1. Extract triplets from a single order PDF
python projects/LawNidhi/cli.py graph-extract-order projects/LawNidhi/data/orders/070110900591-2019_01-07-2025_order.pdf --ingest

# 2. Sync all order PDFs in data/orders/
python projects/LawNidhi/cli.py graph-sync-orders

# 3. Query precedents and statutes for the case
python projects/LawNidhi/cli.py graph-precedents "606/2018"

# 4. Run entire pytest suite
PYTHONPATH=projects/LawNidhi python3 -m pytest projects/LawNidhi/tests/ -v
```
