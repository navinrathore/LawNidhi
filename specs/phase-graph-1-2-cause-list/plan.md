# Phase 1.2 Technical Plan: Cause List Temporal Knowledge Graph

## Component Architecture

```
projects/LawNidhi/lawnidhi/graph/
├── __init__.py          # Export ingest_schedule_to_graph and new models
├── schema.py            # Update EntityType, RelationType, and normalize_hearing_id
├── cause_list.py        # ScheduleModel -> Knowledge Graph conversion & temporal linking
└── store.py             # Temporal queries: listing history, last/next, daily board, clashes
```

## Detailed Implementation Steps

### Step 1: Update `lawnidhi/graph/schema.py`
1. Add `"HEARING"` to `EntityType`.
2. Add `"LISTED_AT"`, `"HELD_IN"`, `"APPEARED_IN"`, `"FOLLOWS_HEARING"` to `RelationType`.
3. Add `normalize_hearing_id(hearing_date: str, court_no: str, list_type: str = "Final") -> str`.

### Step 2: Create `lawnidhi/graph/cause_list.py`
1. Implement `ingest_schedule_to_graph(schedule: ScheduleModel, store: LegalGraphStore) -> Dict[str, int]`:
   - Create `HEARING` entity: `id = normalize_hearing_id(schedule.date, schedule.court_no, schedule.list_type)`.
   - Create `JUDGE` entity: `LegalEntity.create(schedule.judge_name, "JUDGE")`.
   - Create `RelatesTo(HEARING -> PRESIDED_BY -> JUDGE)`.
   - Iterate through `schedule.cases` with `enumerate(..., start=1)`:
     - Formulate case ID: `case_oa_<num>_<year>` or `case_diary_<num>`.
     - Insert `CASE` node.
     - Link `RelatesTo(CASE -> LISTED_AT {item_number, list_type} -> HEARING)`.
     - For each `counsel`, insert `COUNSEL` node, link `COUNSEL -> REPRESENTS -> CASE` and `COUNSEL -> APPEARED_IN -> HEARING`.
     - For each `party`, insert `PARTY` node and link `PARTY -> PARTY_TO -> CASE`.
     - **Temporal Chaining**: Query all prior hearings for this case from `store`. Identify the immediately preceding hearing by date, and create `RelatesTo(New_Hearing -> FOLLOWS_HEARING {days_gap} -> Prior_Hearing)`.

### Step 3: Add Temporal Query Methods to `LegalGraphStore` (`store.py`)
1. `get_case_listing_history(case_id_or_number: str)`:
   - Match `(c:LegalEntity)-[l:RelatesTo {relation_type: 'LISTED_AT'}]->(h:LegalEntity {entity_type: 'HEARING'})`.
   - Optional match `(h)-[:RelatesTo {relation_type: 'PRESIDED_BY'}]->(j:LegalEntity)`.
   - Sort hearings ascending by `h.properties.date`.
   - Compute intervals/days gap between successive hearings.
2. `get_last_and_next_listing(case_id: str, ref_date: Optional[str] = None)`:
   - Compare hearing dates relative to `ref_date` (defaults to current date).
   - Return `{ "previous_listing": ..., "next_listing": ..., "total_listings": N }`.
3. `get_cases_listed_on_date(hearing_date: str, court_no: Optional[str] = None)`:
   - Match `(c:LegalEntity)-[l:RelatesTo {relation_type: 'LISTED_AT'}]->(h:LegalEntity {entity_type: 'HEARING'})` where `h.properties.date = $date`.
   - Return cases ordered by `l.properties.item_number`.
4. `find_counsel_clashes(hearing_date: str, counsel_id_or_name: str)`:
   - Find all hearings on `hearing_date` where the counsel appeared.
   - If `count(DISTINCT h.properties.court_no) > 1`, return the clashing hearings, courtroom numbers, and case names.

### Step 4: Unit Testing (`tests/test_cause_list_graph.py`)
- Test single schedule ingestion.
- Test multi-date schedule ingestion for the same case and verify `FOLLOWS_HEARING` edge creation and `days_gap`.
- Test `get_case_listing_history` and `get_last_and_next_listing`.
- Test daily board ordering and counsel courtroom clash detection.
