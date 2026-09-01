"""store.py: Embedded Knowledge Graph Store using Kùzu."""
from __future__ import annotations
import json
import logging
import os
import sqlite3
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import kuzu
import networkx as nx

from lawnidhi.graph.schema import (
    LegalEntity,
    LegalRelation,
    GraphExtraction,
    normalize_entity_id,
)

logger = logging.getLogger(__name__)


class LegalGraphStore:
    """Embedded Property Graph engine for LawNidhi backed by Kùzu.
    
    Provides high-performance, in-process Cypher querying for legal entities,
    court orders, judge/bench relationships, and precedent citations.
    """

    def __init__(self, db_path: str = "data/lawnidhi_graph/kuzu_db"):
        """Initialize the Kùzu graph database.
        
        Args:
            db_path: Path to the Kùzu database file/directory.
        """
        parent_dir = os.path.dirname(os.path.abspath(db_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self) -> None:
        """Create Node and Rel tables idempotently."""
        try:
            # 1. LegalEntity Node Table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS LegalEntity (
                    id STRING,
                    name STRING,
                    entity_type STRING,
                    properties STRING,
                    PRIMARY KEY (id)
                )
            """)
            # 2. RelatesTo Edge Table
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS RelatesTo (
                    FROM LegalEntity TO LegalEntity,
                    relation_type STRING,
                    weight DOUBLE,
                    properties STRING
                )
            """)
        except Exception as e:
            logger.error(f"Error initializing graph schema: {e}")
            raise

    def insert_entity(self, entity: LegalEntity) -> None:
        """Insert or update a LegalEntity node."""
        try:
            check_res = self.conn.execute(
                "MATCH (n:LegalEntity {id: $id}) RETURN n.id",
                {"id": entity.id}
            )
            if check_res.has_next():
                self.conn.execute(
                    "MATCH (n:LegalEntity {id: $id}) SET n.name = $name, n.entity_type = $type, n.properties = $props",
                    {"id": entity.id, "name": entity.name, "type": entity.entity_type, "props": entity.properties_json()}
                )
            else:
                self.conn.execute(
                    "CREATE (n:LegalEntity {id: $id, name: $name, entity_type: $type, properties: $props})",
                    {"id": entity.id, "name": entity.name, "type": entity.entity_type, "props": entity.properties_json()}
                )
        except Exception as e:
            logger.debug(f"Entity upsert: {e}")

    def insert_relation(self, relation: LegalRelation) -> None:
        """Insert or update a directed relationship between two entities.
        
        Note: Both source and target nodes must exist in the database.
        """
        try:
            case_id = relation.properties.get("case_id") if relation.properties else None
            if case_id:
                check_res = self.conn.execute(
                    "MATCH (a:LegalEntity {id: $src})-[r:RelatesTo {relation_type: $rel}]->(b:LegalEntity {id: $tgt}) "
                    "WHERE r.properties CONTAINS $case_id RETURN r.relation_type",
                    {"src": relation.source_id, "tgt": relation.target_id, "rel": relation.relation_type, "case_id": case_id}
                )
                if check_res.has_next():
                    self.conn.execute(
                        "MATCH (a:LegalEntity {id: $src})-[r:RelatesTo {relation_type: $rel}]->(b:LegalEntity {id: $tgt}) "
                        "WHERE r.properties CONTAINS $case_id "
                        "SET r.weight = $weight, r.properties = $props",
                        {
                            "src": relation.source_id,
                            "tgt": relation.target_id,
                            "rel": relation.relation_type,
                            "case_id": case_id,
                            "weight": float(relation.weight),
                            "props": relation.properties_json(),
                        }
                    )
                else:
                    self.conn.execute(
                        "MATCH (a:LegalEntity {id: $src}), (b:LegalEntity {id: $tgt}) "
                        "CREATE (a)-[r:RelatesTo {relation_type: $rel, weight: $weight, properties: $props}]->(b)",
                        {
                            "src": relation.source_id,
                            "tgt": relation.target_id,
                            "rel": relation.relation_type,
                            "weight": float(relation.weight),
                            "props": relation.properties_json(),
                        }
                    )
            else:
                check_res = self.conn.execute(
                    "MATCH (a:LegalEntity {id: $src})-[r:RelatesTo {relation_type: $rel}]->(b:LegalEntity {id: $tgt}) RETURN r.relation_type",
                    {"src": relation.source_id, "tgt": relation.target_id, "rel": relation.relation_type}
                )
                if check_res.has_next():
                    self.conn.execute(
                        "MATCH (a:LegalEntity {id: $src})-[r:RelatesTo {relation_type: $rel}]->(b:LegalEntity {id: $tgt}) "
                        "SET r.weight = $weight, r.properties = $props",
                        {
                            "src": relation.source_id,
                            "tgt": relation.target_id,
                            "rel": relation.relation_type,
                            "weight": float(relation.weight),
                            "props": relation.properties_json(),
                        }
                    )
                else:
                    self.conn.execute(
                        "MATCH (a:LegalEntity {id: $src}), (b:LegalEntity {id: $tgt}) "
                        "CREATE (a)-[r:RelatesTo {relation_type: $rel, weight: $weight, properties: $props}]->(b)",
                        {
                            "src": relation.source_id,
                            "tgt": relation.target_id,
                            "rel": relation.relation_type,
                            "weight": float(relation.weight),
                            "props": relation.properties_json(),
                        }
                    )
        except Exception as e:
            logger.debug(f"Relation upsert: {e}")

    def insert_graph_data(self, data: GraphExtraction) -> None:
        """Atomically insert a batch of extracted entities and relationships."""
        for entity in data.entities:
            self.insert_entity(entity)

        for relation in data.relationships:
            self.insert_relation(relation)

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve node attributes by entity ID."""
        query = """
            MATCH (n:LegalEntity {id: $id})
            RETURN n.id, n.name, n.entity_type, n.properties
        """
        response = self.conn.execute(query, {"id": entity_id})
        if response.has_next():
            row = response.get_next()
            props = json.loads(row[3]) if row[3] else {}
            return {
                "id": row[0],
                "name": row[1],
                "entity_type": row[2],
                "properties": props,
            }
        return None

    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find all 1-hop outgoing and incoming neighbors for an entity."""
        if relation_type:
            query = """
                MATCH (n:LegalEntity {id: $id})-[r:RelatesTo {relation_type: $rel}]->(target:LegalEntity)
                RETURN target.id, target.name, target.entity_type, r.relation_type, 'OUTGOING' AS direction
                UNION
                MATCH (source:LegalEntity)-[r:RelatesTo {relation_type: $rel}]->(n:LegalEntity {id: $id})
                RETURN source.id, source.name, source.entity_type, r.relation_type, 'INCOMING' AS direction
            """
            params = {"id": entity_id, "rel": relation_type}
        else:
            query = """
                MATCH (n:LegalEntity {id: $id})-[r:RelatesTo]->(target:LegalEntity)
                RETURN target.id, target.name, target.entity_type, r.relation_type, 'OUTGOING' AS direction
                UNION
                MATCH (source:LegalEntity)-[r:RelatesTo]->(n:LegalEntity {id: $id})
                RETURN source.id, source.name, source.entity_type, r.relation_type, 'INCOMING' AS direction
            """
            params = {"id": entity_id}

        response = self.conn.execute(query, params)
        results = []
        while response.has_next():
            row = response.get_next()
            results.append({
                "neighbor_id": row[0],
                "name": row[1],
                "entity_type": row[2],
                "relation_type": row[3],
                "direction": row[4],
            })
        return results

    def find_connected_precedents(self, case_id: str) -> List[Dict[str, Any]]:
        """Multi-hop traversal: Find all cited precedents and invoked statutes for a case."""
        query = """
            MATCH (c:LegalEntity {id: $case_id})-[r1:RelatesTo]->(target:LegalEntity)
            WHERE r1.relation_type IN ['CITES_PRECEDENT', 'INVOKES_STATUTE']
            OPTIONAL MATCH (target)-[r2:RelatesTo]->(sub_target:LegalEntity)
            RETURN target.id, target.name, target.entity_type, r1.relation_type, 
                   sub_target.id, sub_target.name, sub_target.entity_type, r2.relation_type
        """
        response = self.conn.execute(query, {"case_id": case_id})
        results = []
        while response.has_next():
            row = response.get_next()
            results.append({
                "target_id": row[0],
                "target_name": row[1],
                "target_type": row[2],
                "relation": row[3],
                "sub_target_id": row[4] if row[4] else None,
                "sub_target_name": row[5] if row[5] else None,
                "sub_target_type": row[6] if row[6] else None,
                "sub_relation": row[7] if row[7] else None,
            })
        return results

    def find_cases_by_counsel(self, counsel_id_or_name: str) -> List[Dict[str, Any]]:
        """Find all cases where a counsel appeared or is representing a party."""
        counsel_id = normalize_entity_id("COUNSEL", counsel_id_or_name)
        query = """
            MATCH (c:LegalEntity {id: $counsel_id})-[r:RelatesTo {relation_type: 'REPRESENTS'}]->(target:LegalEntity)
            RETURN target.id, target.name, target.entity_type, r.properties
        """
        response = self.conn.execute(query, {"counsel_id": counsel_id})
        results = []
        while response.has_next():
            row = response.get_next()
            props = json.loads(row[3]) if row[3] else {}
            results.append({
                "id": row[0],
                "name": row[1],
                "entity_type": row[2],
                "properties": props,
            })
        return results

    def find_cases_by_judge(self, judge_id_or_name: str) -> List[Dict[str, Any]]:
        """Find all cases presided over by a specific judge."""
        judge_id = normalize_entity_id("JUDGE", judge_id_or_name)
        query = """
            MATCH (c_node:LegalEntity)-[r:RelatesTo {relation_type: 'PRESIDED_BY'}]->(j:LegalEntity {id: $judge_id})
            RETURN c_node.id, c_node.name, c_node.entity_type, r.properties
        """
        response = self.conn.execute(query, {"judge_id": judge_id})
        results = []
        while response.has_next():
            row = response.get_next()
            props = json.loads(row[3]) if row[3] else {}
            results.append({
                "id": row[0],
                "name": row[1],
                "entity_type": row[2],
                "properties": props,
            })
        return results

    def get_case_listing_history(self, case_id_or_number: str) -> List[Dict[str, Any]]:
        """Retrieve the complete chronological hearing sequence for a case.
        
        Returns:
            List of hearings sorted ascending by hearing date with days interval.
        """
        if not case_id_or_number.startswith("case_"):
            clean_str = case_id_or_number if case_id_or_number.upper().startswith("OA") else f"OA {case_id_or_number}"
            case_id = normalize_entity_id("CASE", clean_str)
        else:
            case_id = case_id_or_number

        resolved_case_id = None

        # 1. Direct match by candidate ID
        direct_match = self.conn.execute("MATCH (c:LegalEntity {id: $id, entity_type: 'CASE'}) RETURN c.id", {"id": case_id})
        if direct_match.has_next():
            resolved_case_id = direct_match.get_next()[0]
        else:
            # 2. Substring search on case name or ID
            search_str = case_id_or_number.replace("/", "_").lower().strip()
            search_raw = case_id_or_number.strip()
            fuzzy_match = self.conn.execute(
                "MATCH (c:LegalEntity {entity_type: 'CASE'}) WHERE c.id CONTAINS $s_str OR c.name CONTAINS $s_raw RETURN c.id LIMIT 1",
                {"s_str": search_str, "s_raw": search_raw}
            )
            if fuzzy_match.has_next():
                resolved_case_id = fuzzy_match.get_next()[0]

        if not resolved_case_id:
            return []

        query = """
            MATCH (c:LegalEntity {id: $case_id})-[l:RelatesTo {relation_type: 'LISTED_AT'}]->(h:LegalEntity {entity_type: 'HEARING'})
            OPTIONAL MATCH (h)-[:RelatesTo {relation_type: 'PRESIDED_BY'}]->(j:LegalEntity)
            RETURN h.id, h.name, h.properties, l.properties, j.id, j.name
        """
        response = self.conn.execute(query, {"case_id": resolved_case_id})
        raw_hearings = []
        while response.has_next():
            row = response.get_next()
            h_props = json.loads(row[2]) if row[2] else {}
            l_props = json.loads(row[3]) if row[3] else {}
            raw_hearings.append({
                "hearing_id": row[0],
                "hearing_name": row[1],
                "date": h_props.get("date", ""),
                "court_no": h_props.get("court_no", ""),
                "list_type": l_props.get("list_type", h_props.get("list_type", "Final")),
                "item_number": l_props.get("item_number", None),
                "judge_id": row[4] if row[4] else None,
                "judge_name": row[5] if row[5] else h_props.get("judge_name", None),
            })

        # Sort hearings chronologically ascending
        raw_hearings.sort(key=lambda h: h["date"] or "")

        # Compute interval between successive hearings
        prev_date = None
        for h in raw_hearings:
            if h["date"]:
                try:
                    curr_d = datetime.strptime(h["date"][:10], "%Y-%m-%d").date()
                    if prev_date:
                        h["days_since_previous"] = (curr_d - prev_date).days
                    else:
                        h["days_since_previous"] = None
                    prev_date = curr_d
                except ValueError:
                    h["days_since_previous"] = None
            else:
                h["days_since_previous"] = None

        return raw_hearings

    def get_last_and_next_listing(
        self,
        case_id_or_number: str,
        ref_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find the immediate previous and scheduled next listing relative to a reference date.
        
        Args:
            case_id_or_number: Case ID or number (e.g. '83/2025' or 'case_oa_83_2025').
            ref_date: ISO date string 'YYYY-MM-DD' (defaults to current local date).
            
        Returns:
            Dict containing previous_listing, next_listing, and total_hearings.
        """
        history = self.get_case_listing_history(case_id_or_number)
        if not history:
            return {
                "case_id": case_id_or_number,
                "total_hearings": 0,
                "previous_listing": None,
                "next_listing": None,
                "days_since_last_hearing": None,
            }

        ref_d = datetime.strptime(ref_date[:10], "%Y-%m-%d").date() if ref_date else datetime.now().date()

        past_hearings = []
        future_hearings = []

        for h in history:
            if not h["date"]:
                continue
            try:
                h_date = datetime.strptime(h["date"][:10], "%Y-%m-%d").date()
                if h_date <= ref_d:
                    past_hearings.append((h_date, h))
                else:
                    future_hearings.append((h_date, h))
            except ValueError:
                continue

        past_hearings.sort(key=lambda x: x[0], reverse=True)
        future_hearings.sort(key=lambda x: x[0])

        prev_listing = past_hearings[0][1] if past_hearings else None
        next_listing = future_hearings[0][1] if future_hearings else None

        days_gap = None
        if prev_listing and prev_listing["date"]:
            prev_d = datetime.strptime(prev_listing["date"][:10], "%Y-%m-%d").date()
            days_gap = (ref_d - prev_d).days

        return {
            "case_id": case_id_or_number,
            "total_hearings": len(history),
            "reference_date": ref_d.isoformat(),
            "previous_listing": prev_listing,
            "next_listing": next_listing,
            "days_since_last_hearing": days_gap,
        }

    def get_cases_listed_on_date(
        self,
        hearing_date: str,
        court_no: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all cases listed on a specific date, ordered by item number."""
        clean_date = str(hearing_date)[:10]
        query = """
            MATCH (c:LegalEntity {entity_type: 'CASE'})-[l:RelatesTo {relation_type: 'LISTED_AT'}]->(h:LegalEntity {entity_type: 'HEARING'})
            OPTIONAL MATCH (h)-[:RelatesTo {relation_type: 'PRESIDED_BY'}]->(j:LegalEntity)
            RETURN c.id, c.name, l.properties, h.id, h.properties, j.name
        """
        response = self.conn.execute(query, {})
        
        # Build map of (case_id, hearing_id) -> list of counsel names
        counsel_query = """
            MATCH (counsel:LegalEntity {entity_type: 'COUNSEL'})-[r:RelatesTo {relation_type: 'APPEARED_IN'}]->(h:LegalEntity {entity_type: 'HEARING'})
            RETURN counsel.name, h.id, r.properties
        """
        c_res = self.conn.execute(counsel_query, {})
        counsel_map = {}
        while c_res.has_next():
            c_row = c_res.get_next()
            c_name, h_id, r_props_str = c_row[0], c_row[1], c_row[2]
            r_props = json.loads(r_props_str) if r_props_str else {}
            cid = r_props.get("case_id")
            if cid:
                key = (cid, h_id)
                if c_name not in counsel_map.setdefault(key, []):
                    counsel_map[key].append(c_name)

        cases = []
        while response.has_next():
            row = response.get_next()
            l_props = json.loads(row[2]) if row[2] else {}
            h_id = row[3]
            h_props = json.loads(row[4]) if row[4] else {}
            
            h_date = h_props.get("date", "")
            h_court = h_props.get("court_no", "")
            
            if h_date == clean_date:
                if court_no is None or court_no.lower() in h_court.lower():
                    case_id = row[0]
                    counsels_list = counsel_map.get((case_id, h_id), [])
                    counsels_str = ", ".join(counsels_list) if counsels_list else "-"
                    cases.append({
                        "case_id": case_id,
                        "case_name": row[1],
                        "item_number": l_props.get("item_number", 999),
                        "list_type": l_props.get("list_type", "Final"),
                        "court_no": h_court,
                        "counsels": counsels_str,
                        "judge_name": row[5] or h_props.get("judge_name", ""),
                    })

        cases.sort(key=lambda x: (x["court_no"], x["item_number"]))
        return cases

    def find_counsel_clashes(
        self,
        hearing_date: str,
        counsel_id_or_name: str
    ) -> List[Dict[str, Any]]:
        """Identify if a counsel has simultaneous appearances across different courtrooms on the same date."""
        counsel_id = normalize_entity_id("COUNSEL", counsel_id_or_name)
        clean_date = str(hearing_date)[:10]

        query = """
            MATCH (counsel:LegalEntity {id: $counsel_id})-[r:RelatesTo {relation_type: 'APPEARED_IN'}]->(h:LegalEntity {entity_type: 'HEARING'})
            OPTIONAL MATCH (c_node:LegalEntity)-[l:RelatesTo {relation_type: 'LISTED_AT'}]->(h)
            WHERE counsel.id = $counsel_id
            RETURN h.id, h.name, h.properties, r.properties, c_node.id, c_node.name, l.properties
        """
        response = self.conn.execute(query, {"counsel_id": counsel_id})
        appearances = []
        courtrooms = set()

        while response.has_next():
            row = response.get_next()
            h_props = json.loads(row[2]) if row[2] else {}
            r_props = json.loads(row[3]) if row[3] else {}
            l_props = json.loads(row[6]) if row[6] else {}

            if h_props.get("date") == clean_date:
                court = h_props.get("court_no", "")
                courtrooms.add(court)
                appearances.append({
                    "hearing_id": row[0],
                    "court_no": court,
                    "case_id": row[4],
                    "case_name": row[5],
                    "item_number": l_props.get("item_number", r_props.get("item_number")),
                    "judge_name": h_props.get("judge_name", ""),
                })

        # If listed in more than 1 courtroom, flag as clash
        if len(courtrooms) > 1:
            appearances.sort(key=lambda x: (x["court_no"], x.get("item_number") or 999))
            return appearances
        return []

    def get_counsel_schedule(
        self,
        counsel_id_or_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve all scheduled case appearances for a counsel within an optional date range.
        
        Args:
            counsel_id_or_name: Counsel name (e.g. 'Bhanwar Pal Singh') or normalized ID.
            start_date: Start date 'YYYY-MM-DD' (inclusive).
            end_date: End date 'YYYY-MM-DD' (inclusive).
            
        Returns:
            List of appearances sorted by date, court_no, item_number.
        """
        counsel_id = normalize_entity_id("COUNSEL", counsel_id_or_name)
        # 1. Match all counsel nodes that match ID or name
        clean_search = counsel_id_or_name.replace(".", " ").strip().lower()
        tokens = [t for t in clean_search.split() if len(t) > 2]
        token_pattern = tokens[0] if tokens else clean_search

        counsel_matches = self.conn.execute(
            "MATCH (c:LegalEntity {entity_type: 'COUNSEL'}) WHERE c.id CONTAINS $pat OR c.id CONTAINS $cid OR c.name CONTAINS $raw RETURN c.id, c.name",
            {"pat": token_pattern, "cid": counsel_id, "raw": counsel_id_or_name.strip()}
        )
        
        matched_counsels = []
        while counsel_matches.has_next():
            row = counsel_matches.get_next()
            matched_counsels.append((row[0], row[1]))

        if not matched_counsels:
            return []

        appearances = []
        seen_entries = set()

        for cid, cname in matched_counsels:
            if start_date or end_date:
                # 1. Date-specific board: Query direct assigned appearances on that specific hearing
                query = """
                    MATCH (counsel:LegalEntity {id: $counsel_id})-[r:RelatesTo {relation_type: 'APPEARED_IN'}]->(h:LegalEntity {entity_type: 'HEARING'})
                    OPTIONAL MATCH (h)-[:RelatesTo {relation_type: 'PRESIDED_BY'}]->(j:LegalEntity)
                    RETURN h.id, h.name, h.properties, r.properties, j.name
                """
                response = self.conn.execute(query, {"counsel_id": cid})

                while response.has_next():
                    row = response.get_next()
                    h_props = json.loads(row[2]) if row[2] else {}
                    r_props = json.loads(row[3]) if row[3] else {}

                    h_date = h_props.get("date", "")
                    if start_date and h_date < start_date[:10]:
                        continue
                    if end_date and h_date > end_date[:10]:
                        continue

                    case_id = r_props.get("case_id", "")
                    case_entity = self.get_entity(case_id) if case_id else None
                    case_name = case_entity["name"] if case_entity else (case_id or "Case")
                    court_no = h_props.get("court_no", "")
                    item_no = r_props.get("item_number", None)
                    list_type = h_props.get("list_type", "Final")

                    entry_key = (h_date, court_no, item_no, case_id, list_type)
                    if entry_key in seen_entries:
                        continue
                    seen_entries.add(entry_key)

                    appearances.append({
                        "counsel_id": cid,
                        "counsel_name": cname,
                        "hearing_id": row[0],
                        "date": h_date,
                        "court_no": court_no,
                        "list_type": list_type,
                        "case_id": case_id,
                        "case_name": case_name,
                        "item_number": item_no,
                        "judge_name": row[4] or h_props.get("judge_name", ""),
                    })
            else:
                # 2. Historical/lifetime query: Traverse all lifetime case representations
                query = """
                    MATCH (counsel:LegalEntity {id: $counsel_id})-[r:RelatesTo {relation_type: 'REPRESENTS'}]->(c_node:LegalEntity {entity_type: 'CASE'})-[l:RelatesTo {relation_type: 'LISTED_AT'}]->(h:LegalEntity {entity_type: 'HEARING'})
                    OPTIONAL MATCH (h)-[:RelatesTo {relation_type: 'PRESIDED_BY'}]->(j:LegalEntity)
                    RETURN h.id, h.name, h.properties, c_node.id, c_node.name, l.properties, j.name
                """
                response = self.conn.execute(query, {"counsel_id": cid})

                while response.has_next():
                    row = response.get_next()
                    h_props = json.loads(row[2]) if row[2] else {}
                    l_props = json.loads(row[5]) if row[5] else {}

                    h_date = h_props.get("date", "")
                    case_id = row[3]
                    case_name = row[4]
                    court_no = h_props.get("court_no", "")
                    item_no = l_props.get("item_number", None)
                    list_type = l_props.get("list_type", h_props.get("list_type", "Final"))

                    entry_key = (h_date, court_no, item_no, case_id, list_type)
                    if entry_key in seen_entries:
                        continue
                    seen_entries.add(entry_key)

                    appearances.append({
                        "counsel_id": cid,
                        "counsel_name": cname,
                        "hearing_id": row[0],
                        "date": h_date,
                        "court_no": court_no,
                        "list_type": list_type,
                        "case_id": case_id,
                        "case_name": case_name,
                        "item_number": item_no,
                        "judge_name": row[6] or h_props.get("judge_name", ""),
                    })

        appearances.sort(key=lambda x: (x["date"], x["court_no"], x.get("item_number") or 999))
        return appearances

    def export_networkx_graph(self) -> nx.DiGraph:
        """Export the entire Kùzu graph into a NetworkX directed graph for topological analysis."""
        G = nx.DiGraph()

        # 1. Fetch all nodes
        node_res = self.conn.execute("MATCH (n:LegalEntity) RETURN n.id, n.name, n.entity_type, n.properties")
        while node_res.has_next():
            row = node_res.get_next()
            props = json.loads(row[3]) if row[3] else {}
            G.add_node(row[0], name=row[1], entity_type=row[2], **props)

        # 2. Fetch all edges
        rel_res = self.conn.execute("""
            MATCH (a:LegalEntity)-[r:RelatesTo]->(b:LegalEntity)
            RETURN a.id, b.id, r.relation_type, r.weight, r.properties
        """)
        while rel_res.has_next():
            row = rel_res.get_next()
            props = json.loads(row[4]) if row[4] else {}
            G.add_edge(row[0], row[1], relation_type=row[2], weight=row[3], **props)

        return G

    def sync_from_sqlite(self, sqlite_db_path: str) -> int:
        """Synchronize cases, counsels, and parties from LawNidhi's SQLite database.
        
        Returns:
            int: Number of cases synchronized.
        """
        if not os.path.exists(sqlite_db_path):
            logger.warning(f"SQLite DB not found at {sqlite_db_path}")
            return 0

        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Fetch cases
        try:
            cursor.execute("SELECT id, case_number, case_year, diary_number FROM cases")
            cases = cursor.fetchall()
        except sqlite3.OperationalError:
            cases = []

        count = 0
        for case in cases:
            case_name = f"OA {case['case_number']}/{case['case_year']}" if case['case_number'] else f"Diary {case['diary_number']}"
            case_entity = LegalEntity.create(
                name=case_name,
                entity_type="CASE",
                properties={
                    "case_number": case["case_number"],
                    "case_year": case["case_year"],
                    "diary_number": case["diary_number"],
                    "sqlite_id": case["id"],
                }
            )
            self.insert_entity(case_entity)
            count += 1

            # Sync counsels for this case
            try:
                cursor.execute("""
                    SELECT c.name FROM counsels c
                    JOIN case_counsels cc ON c.id = cc.counsel_id
                    WHERE cc.case_id = ?
                """, (case["id"],))
                counsels = cursor.fetchall()
                for c in counsels:
                    counsel_ent = LegalEntity.create(name=c["name"], entity_type="COUNSEL")
                    self.insert_entity(counsel_ent)
                    self.insert_relation(LegalRelation(
                        source_id=counsel_ent.id,
                        relation_type="REPRESENTS",
                        target_id=case_entity.id
                    ))
            except sqlite3.OperationalError:
                pass

            # Sync parties for this case
            try:
                cursor.execute("SELECT name, role FROM parties WHERE case_id = ?", (case["id"],))
                parties = cursor.fetchall()
                for p in parties:
                    party_ent = LegalEntity.create(name=p["name"], entity_type="PARTY", properties={"role": p["role"]})
                    self.insert_entity(party_ent)
                    self.insert_relation(LegalRelation(
                        source_id=party_ent.id,
                        relation_type="PARTY_TO",
                        target_id=case_entity.id
                    ))
            except sqlite3.OperationalError:
                pass

        conn.close()
        return count

    def get_graph_stats(self) -> Dict[str, Any]:
        """Compute aggregate statistics of the knowledge graph."""
        node_res = self.conn.execute("MATCH (n:LegalEntity) RETURN count(n)")
        total_nodes = node_res.get_next()[0] if node_res.has_next() else 0

        rel_res = self.conn.execute("MATCH ()-[r:RelatesTo]->() RETURN count(r)")
        total_rels = rel_res.get_next()[0] if rel_res.has_next() else 0

        type_res = self.conn.execute("MATCH (n:LegalEntity) RETURN n.entity_type, count(n)")
        type_breakdown: Dict[str, int] = {}
        while type_res.has_next():
            row = type_res.get_next()
            type_breakdown[row[0]] = row[1]

        return {
            "total_nodes": total_nodes,
            "total_relationships": total_rels,
            "entity_breakdown": type_breakdown,
        }

    def close(self) -> None:
        """Close connection and free resources."""
        pass

    def __enter__(self) -> LegalGraphStore:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
