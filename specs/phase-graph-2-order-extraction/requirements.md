# Phase 2 Requirements: PDF Order Triplet Extraction & Precedent Citation Graph

## Objective
Extract structured legal knowledge triplets (invoked statutes, cited precedents, bench members, directions, and penalties) from unstructured NGT judicial order PDFs and ingest them into the Kùzu Property Graph.

## Background & Problem
While Cause Lists provide operational metadata (courtrooms, item numbers, scheduled advocates), the actual legal arguments, statutory foundations, and binding precedents reside inside judicial **Orders & Judgments** (PDF format). 

To power precedent research, litigation intelligence, and GraphRAG retrieval:
1. Every order PDF must be parsed to extract the case coram, date, and body text.
2. Statutory provisions (e.g. *Section 14/15/20 of the NGT Act 2010*, *Section 21 of the Air Act 1981*, *Section 25 of the Water Act 1974*, *EIA Notification 2006*) must be deterministically parsed with $0$ LLM token tax.
3. Precedent citations (e.g. *Vellore Citizens Welfare Forum (1996) 5 SCC 647*, *M.C. Mehta v. Union of India*) and substantive directions must be extracted via a schema-enforced hybrid supervisory wrapper.
4. Extracted nodes (`STATUTE`, `SECTION`, `CASE`, `DIRECTION`, `PENALTY`) and relationships (`INVOKES_STATUTE`, `CITES_PRECEDENT`, `ISSUED_DIRECTION`, `DELIVERED_BY`) must be linked to the core `CASE` node in Kùzu DB.

## Architectural Principles (Rules & Guidelines)
- **Rule 11 (Hybrid Supervisory Wrapper Pattern)**: Deterministic regex extractors run first with $0$ LLM latency/token overhead. The LLM acts exclusively as an optional supervisory enrichment layer.
- **Provider Agnosticism**: Abstract any LLM calling through `BaseLLMClient` to ensure OpenAI/Anthropic/Bedrock/Gemini interchangeability.
- **Structured Schema Enforcement**: Use Pydantic models for structured output validation at the API boundary.

## Functional Requirements

### 1. Order PDF Text Extractor (`order_extractor.py`)
- Extract clean text from multi-page NGT Order PDFs (`pdfplumber`/`pypdf`).
- Parse standard header metadata: Case Number, Order Date, Bench Judges / Coram.

### 2. Deterministic Statutory Section Matcher (`statute_parser.py`)
- High-precision regex pattern matchers for Indian Environmental Statutes:
  - National Green Tribunal Act, 2010 (Sec 14, 15, 18, 19, 20, 26).
  - Water (Prevention & Control of Pollution) Act, 1974 (Sec 24, 25, 33A).
  - Air (Prevention & Control of Pollution) Act, 1981 (Sec 21, 31A).
  - Environment (Protection) Act, 1986 (Sec 3, 5).
  - Forest (Conservation) Act, 1980 / Biological Diversity Act, 2002.
  - EIA Notification, 2006 / CRZ Notification.

### 3. Precedent & Direction Extraction Model (`schema.py`)
- Define `OrderExtractionResult` Pydantic model:
  - `case_id`: Canonical Case ID.
  - `order_date`: Date of the judicial order.
  - `bench_judges`: List of presiding judges.
  - `invoked_statutes`: List of statutory references (`act_name`, `section`).
  - `cited_precedents`: List of precedent citations (`case_title`, `citation`, `court`).
  - `directions`: List of key directions or penalties issued.

### 4. Graph Ingestion Pipeline (`lawnidhi/graph/order_sync.py`)
- Merge extracted entities into `LegalGraphStore`.
- Construct edges:
  - `(Case)-[:INVOKES_STATUTE]->(Statute/Section)`
  - `(Case)-[:CITES_PRECEDENT]->(Precedent_Case)`
  - `(Case)-[:ISSUED_DIRECTION]->(Direction)`
  - `(Case)-[:DELIVERED_BY]->(Judge)`

### 5. CLI Commands
- `python projects/LawNidhi/cli.py graph-extract-order <pdf_path> [--ingest]`
- `python projects/LawNidhi/cli.py graph-sync-orders [--dir <orders_dir>]`
