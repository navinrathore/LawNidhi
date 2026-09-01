# Phase 1.2 Requirements: Cause List Temporal Knowledge Graph & Listing Intelligence

## Objective
Extend LawNidhi's Knowledge Graph to ingest and model daily NGT cause lists, enabling temporal graph analytics such as chronological case listing histories, previous/next hearing intervals, daily courtroom board queries, and counsel courtroom clash detection.

## Background
LawNidhi's scraper and parsers automatically download and extract daily hearing schedules into `ScheduleModel` instances. By modeling these schedules as `HEARING` nodes connected to `CASE`, `JUDGE`, and `COUNSEL` entities, we can build a dynamic listing history graph without requiring any LLM token consumption.

## Requirements

### 1. Schema Additions (`schema.py`)
- **Entity Types**:
  - `HEARING`: Represents a specific court session on a date in a particular courtroom.
- **Relation Types**:
  - `LISTED_AT`: Links a `CASE` to a `HEARING` with properties `item_number` and `list_type`.
  - `PRESIDED_BY`: Links a `HEARING` to a `JUDGE`.
  - `HELD_IN`: Links a `HEARING` to a `BENCH` or `COURT`.
  - `APPEARED_IN`: Links a `COUNSEL` to a `HEARING`.
  - `FOLLOWS_HEARING`: Directed temporal link between a later `HEARING` and an earlier `HEARING` for the same case with property `days_gap`.

### 2. Cause List Ingestor (`cause_list.py`)
- Ingest a `ScheduleModel` into `LegalGraphStore`.
- Create or update `HEARING` nodes and associated `JUDGE`, `CASE`, `COUNSEL`, and `PARTY` nodes.
- Traverse prior hearings of each case to link chronological chains via `FOLLOWS_HEARING`.

### 3. Query & Analytics APIs (`store.py`)
- `get_case_listing_history(case_id)`: Retrieve all hearings for a case in chronological order.
- `get_last_and_next_listing(case_id, ref_date)`: Return the previous hearing and upcoming hearing relative to `ref_date`.
- `get_cases_listed_on_date(date, court_no)`: Return all cases listed on a given date sorted by `item_number`.
- `find_counsel_clashes(date, counsel_name)`: Identify if a counsel is listed in multiple distinct courtrooms on the same date.

### 4. Unit Test Suite (`tests/test_cause_list_graph.py`)
- Validate schedule ingestion, temporal chaining, history queries, and clash detection.
