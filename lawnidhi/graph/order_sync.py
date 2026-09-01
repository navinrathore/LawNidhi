"""order_sync.py: Synchronize extracted order triplets (statutes, precedents, coram) into Kùzu Knowledge Graph."""
from __future__ import annotations
import glob
import os
from typing import Dict, List, Any
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import (
    LegalEntity,
    LegalRelation,
    OrderExtractionResult,
    normalize_entity_id
)
from lawnidhi.parsers.ngt.order_parser import NGTOrderParser


def ingest_order_extraction(store: LegalGraphStore, extraction: OrderExtractionResult) -> Dict[str, int]:
    """Ingest structured triplets from an order extraction result into the Kùzu Graph."""
    stats = {"nodes_added": 0, "relations_added": 0}

    # 1. Resolve or create Case Node
    resolved_id = store.resolve_case_id(extraction.case_name)
    case_id = resolved_id or extraction.case_id or normalize_entity_id("CASE", extraction.case_name)

    case_entity = LegalEntity.create(
        name=extraction.case_name,
        entity_type="CASE",
        custom_id=case_id,
        properties={
            "order_date": extraction.order_date,
            "court_number": extraction.court_number,
        }
    )
    store.insert_entity(case_entity)
    stats["nodes_added"] += 1

    # 2. Ingest Coram Judges & DELIVERED_BY edges
    for judge_name in extraction.bench_judges:
        judge_ent = LegalEntity.create(name=judge_name, entity_type="JUDGE")
        store.insert_entity(judge_ent)
        stats["nodes_added"] += 1

        rel = LegalRelation(
            source_id=case_id,
            relation_type="DELIVERED_BY",
            target_id=judge_ent.id,
            properties={"order_date": extraction.order_date}
        )
        store.insert_relation(rel)
        stats["relations_added"] += 1

    # 3. Ingest Invoked Statutes & Sections
    for stat in extraction.invoked_statutes:
        # Create Section entity
        sec_name = f"Section {stat.section}, {stat.act_name}"
        sec_ent = LegalEntity.create(
            name=sec_name,
            entity_type="SECTION",
            properties={"section": stat.section, "act": stat.act_name}
        )
        store.insert_entity(sec_ent)
        stats["nodes_added"] += 1

        # Link Case -> Section
        rel = LegalRelation(
            source_id=case_id,
            relation_type="INVOKES_STATUTE",
            target_id=sec_ent.id,
            properties={"raw_match": stat.raw_match, "act_name": stat.act_name}
        )
        store.insert_relation(rel)
        stats["relations_added"] += 1

    # 4. Ingest Cited Precedents
    for prec in extraction.cited_precedents:
        prec_name = f"{prec.case_title} ({prec.citation})" if prec.citation else prec.case_title
        prec_ent = LegalEntity.create(
            name=prec_name,
            entity_type="CASE",
            properties={
                "citation": prec.citation,
                "court": prec.court,
                "year": prec.year,
                "is_precedent": True,
            }
        )
        store.insert_entity(prec_ent)
        stats["nodes_added"] += 1

        rel = LegalRelation(
            source_id=case_id,
            relation_type="CITES_PRECEDENT",
            target_id=prec_ent.id,
            properties={"citation": prec.citation}
        )
        store.insert_relation(rel)
        stats["relations_added"] += 1

    # 5. Ingest Directions & Penalties
    for direct in extraction.directions:
        etype = "PENALTY" if direct.direction_type == "PENALTY" else "DIRECTION"
        dir_ent = LegalEntity.create(
            name=direct.direction_text[:100],
            entity_type=etype,
            properties={
                "direction_type": direct.direction_type,
                "full_text": direct.direction_text,
                "target_entity": direct.target_entity,
            }
        )
        store.insert_entity(dir_ent)
        stats["nodes_added"] += 1

        rel_type = "IMPOSED_PENALTY" if direct.direction_type == "PENALTY" else "ISSUED_DIRECTION"
        rel = LegalRelation(
            source_id=case_id,
            relation_type=rel_type,
            target_id=dir_ent.id,
            properties={"direction_type": direct.direction_type}
        )
        store.insert_relation(rel)
        stats["relations_added"] += 1

    return stats


def sync_all_orders(store: LegalGraphStore, orders_dir: str) -> Dict[str, Any]:
    """Scan and ingest all judicial order PDFs in a directory into the Knowledge Graph."""
    if not os.path.isdir(orders_dir):
        return {"total_pdfs": 0, "processed": 0, "errors": [f"Directory not found: {orders_dir}"]}

    pdf_files = sorted(glob.glob(os.path.join(orders_dir, "*.pdf")))
    parser = NGTOrderParser()

    total_statutes = 0
    total_precedents = 0
    processed_count = 0
    errors = []

    for pdf_path in pdf_files:
        try:
            extraction = parser.parse_order(pdf_path)
            stats = ingest_order_extraction(store, extraction)
            total_statutes += len(extraction.invoked_statutes)
            total_precedents += len(extraction.cited_precedents)
            processed_count += 1
        except Exception as e:
            errors.append(f"{os.path.basename(pdf_path)}: {str(e)}")

    return {
        "total_pdfs": len(pdf_files),
        "processed": processed_count,
        "total_statutes_extracted": total_statutes,
        "total_precedents_extracted": total_precedents,
        "errors": errors,
    }
