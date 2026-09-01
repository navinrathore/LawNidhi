# Phase 1.2 Validation & Test Plan: Cause List Temporal Knowledge Graph

## Verification Matrix

| Test Function | Description | Expected Outcome |
| :--- | :--- | :--- |
| **`test_ingest_single_schedule`** | Ingest a 1-day `ScheduleModel` with 2 cases, judge, and counsels. | Creates `HEARING`, `CASE`, `JUDGE`, and `COUNSEL` nodes with `LISTED_AT`, `PRESIDED_BY`, and `APPEARED_IN` edges. |
| **`test_temporal_hearing_chain`** | Ingest two schedules on different dates (`2025-01-10` and `2025-03-14`) for the same case (`OA 83/2025`). | Second hearing connects to first via `FOLLOWS_HEARING` with `days_gap = 63`. |
| **`test_case_listing_history`** | Query `get_case_listing_history` for a multi-hearing case. | Returns chronologically ordered list of hearings with dates, court numbers, judges, and intervals. |
| **`test_last_and_next_listing`** | Query `get_last_and_next_listing` with a reference date between two hearings. | Accurately identifies the immediate past hearing and upcoming future hearing. |
| **`test_daily_board_ordering`** | Query `get_cases_listed_on_date` for a specific day. | Returns all cases listed on that date, sorted ascending by `item_number`. |
| **`test_counsel_clash_detection`** | Ingest schedules where the same counsel is listed in `Court 1` and `Court 2` on the same date. | `find_counsel_clashes` flags the multi-courtroom conflict with details of both listings. |

## Execution Command
```bash
PYTHONPATH=projects/LawNidhi python3 -m pytest projects/LawNidhi/tests/test_cause_list_graph.py -v
```
