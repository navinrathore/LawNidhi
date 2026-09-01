"""cause_list.py: Ingest NGT cause list schedules into Knowledge Graph."""
from __future__ import annotations
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional

from lawnidhi.models.core import ScheduleModel, CaseModel
from lawnidhi.graph.schema import (
    LegalEntity,
    LegalRelation,
    normalize_entity_id,
    normalize_hearing_id,
)
from lawnidhi.graph.store import LegalGraphStore

logger = logging.getLogger(__name__)


def _parse_date(val: Any) -> Optional[date]:
    """Helper to convert string/date to datetime.date object."""
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return datetime.strptime(val[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def ingest_schedule_to_graph(
    schedule: ScheduleModel,
    store: LegalGraphStore
) -> Dict[str, int]:
    """Ingest a parsed ScheduleModel into the Knowledge Graph.
    
    Creates:
      - HEARING node (with date, court_no, list_type, judge_name)
      - JUDGE node (linked via PRESIDED_BY)
      - CASE nodes (linked via LISTED_AT with item_number)
      - COUNSEL nodes (linked via APPEARED_IN and REPRESENTS)
      - PARTY nodes (linked via PARTY_TO)
      - FOLLOWS_HEARING temporal edges between successive hearings of the same case
      
    Returns:
      Dict with counts of ingested cases, counsels, and created relations.
    """
    hearing_date_str = schedule.date.isoformat() if hasattr(schedule.date, "isoformat") else str(schedule.date)
    court_no_str = schedule.court_no or "Court 1"
    list_type_str = schedule.list_type or "Final"

    hearing_id = normalize_hearing_id(hearing_date_str, court_no_str, list_type_str)

    # 1. Create/Merge Hearing Node
    hearing_entity = LegalEntity(
        id=hearing_id,
        name=f"Hearing on {hearing_date_str} ({court_no_str})",
        entity_type="HEARING",
        properties={
            "date": hearing_date_str,
            "court_no": court_no_str,
            "list_type": list_type_str,
            "judge_name": schedule.judge_name,
        }
    )
    store.insert_entity(hearing_entity)

    # 2. Create/Merge Judge Node and PRESIDED_BY relation
    if schedule.judge_name:
        judge_entity = LegalEntity.create(name=schedule.judge_name, entity_type="JUDGE")
        store.insert_entity(judge_entity)
        store.insert_relation(LegalRelation(
            source_id=hearing_id,
            relation_type="PRESIDED_BY",
            target_id=judge_entity.id
        ))

    cases_ingested = 0
    counsels_ingested = 0
    relations_created = 1  # at least PRESIDED_BY

    # 3. Ingest each Case in the Cause List
    for item_number, case in enumerate(schedule.cases, start=1):
        if case.case_number and case.case_year:
            case_name = f"OA {case.case_number}/{case.case_year}"
            case_id = normalize_entity_id("CASE", case_name)
        elif case.diary_number:
            case_name = f"Diary {case.diary_number}"
            case_id = normalize_entity_id("CASE", case_name)
        else:
            continue

        case_entity = LegalEntity(
            id=case_id,
            name=case_name,
            entity_type="CASE",
            properties={
                "case_number": case.case_number,
                "case_year": case.case_year,
                "diary_number": case.diary_number,
            }
        )
        store.insert_entity(case_entity)
        cases_ingested += 1

        # Link CASE -> LISTED_AT -> HEARING
        store.insert_relation(LegalRelation(
            source_id=case_id,
            relation_type="LISTED_AT",
            target_id=hearing_id,
            properties={
                "item_number": item_number,
                "list_type": list_type_str,
                "date": hearing_date_str,
            }
        ))
        relations_created += 1

        # 4. Link Counsels
        for counsel in case.counsels:
            if not counsel.name:
                continue
            counsel_entity = LegalEntity.create(name=counsel.name, entity_type="COUNSEL")
            store.insert_entity(counsel_entity)
            counsels_ingested += 1

            # COUNSEL represents CASE
            store.insert_relation(LegalRelation(
                source_id=counsel_entity.id,
                relation_type="REPRESENTS",
                target_id=case_id
            ))
            # COUNSEL appeared in HEARING
            store.insert_relation(LegalRelation(
                source_id=counsel_entity.id,
                relation_type="APPEARED_IN",
                target_id=hearing_id,
                properties={"case_id": case_id, "item_number": item_number}
            ))
            relations_created += 2

        # 5. Link Parties
        for app in case.applicants:
            if app.name:
                app_entity = LegalEntity.create(name=app.name, entity_type="PARTY", properties={"role": "Applicant"})
                store.insert_entity(app_entity)
                store.insert_relation(LegalRelation(
                    source_id=app_entity.id,
                    relation_type="PARTY_TO",
                    target_id=case_id,
                    properties={"role": "Applicant"}
                ))
                relations_created += 1

        for res in case.respondents:
            if res.name:
                res_entity = LegalEntity.create(name=res.name, entity_type="PARTY", properties={"role": "Respondent"})
                store.insert_entity(res_entity)
                store.insert_relation(LegalRelation(
                    source_id=res_entity.id,
                    relation_type="PARTY_TO",
                    target_id=case_id,
                    properties={"role": "Respondent"}
                ))
                relations_created += 1

        # 6. Build Temporal Hearing Chain (FOLLOWS_HEARING)
        # Fetch all hearings linked to this case
        all_hearings = store.get_case_listing_history(case_id)
        if len(all_hearings) > 1:
            current_date = _parse_date(hearing_date_str)
            # Find the immediately preceding hearing
            prior_hearings = [
                h for h in all_hearings 
                if h["date"] and _parse_date(h["date"]) and _parse_date(h["date"]) < current_date
            ]
            if prior_hearings:
                # Sort descending to get the closest past hearing
                prior_hearings.sort(key=lambda h: _parse_date(h["date"]), reverse=True)
                closest_prior = prior_hearings[0]
                prior_date = _parse_date(closest_prior["date"])
                days_gap = (current_date - prior_date).days if (current_date and prior_date) else 0

                store.insert_relation(LegalRelation(
                    source_id=hearing_id,
                    relation_type="FOLLOWS_HEARING",
                    target_id=closest_prior["hearing_id"],
                    properties={"days_gap": days_gap, "case_id": case_id}
                ))
                relations_created += 1

    return {
        "hearing_id": hearing_id,
        "cases_ingested": cases_ingested,
        "counsels_ingested": counsels_ingested,
        "relations_created": relations_created,
    }
