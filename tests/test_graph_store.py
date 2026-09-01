"""test_graph_store.py: Unit tests for LawNidhi Knowledge Graph Engine."""
import os
import sqlite3
import pytest
import networkx as nx
from lawnidhi.graph.schema import (
    LegalEntity,
    LegalRelation,
    GraphExtraction,
    normalize_entity_id,
)
from lawnidhi.graph.store import LegalGraphStore


@pytest.fixture
def graph_store(tmp_path):
    """Fixture providing a temporary LegalGraphStore instance."""
    db_path = str(tmp_path / "kuzu_test_db")
    store = LegalGraphStore(db_path=db_path)
    yield store
    store.close()


def test_schema_normalization():
    """Verify entity ID normalization rules."""
    assert normalize_entity_id("CASE", "OA 83/2025") == "case_oa_83_2025"
    assert normalize_entity_id("COUNSEL", "Adv. Sanjay Upadhyay") == "counsel_sanjay_upadhyay"
    assert normalize_entity_id("JUDGE", "Hon'ble Justice Prakash Shrivastava") == "judge_prakash_shrivastava"
    assert normalize_entity_id("STATUTE", "NGT Act, 2010 (Sec 14)") == "statute_ngt_act_2010_sec_14"

    # Test factory helper
    entity = LegalEntity.create(
        name="Adv. Sanjay Upadhyay",
        entity_type="COUNSEL",
        properties={"chamber": "New Delhi"}
    )
    assert entity.id == "counsel_sanjay_upadhyay"
    assert entity.name == "Adv. Sanjay Upadhyay"
    assert entity.entity_type == "COUNSEL"
    assert entity.properties["chamber"] == "New Delhi"


def test_store_init(graph_store):
    """Verify that graph store initializes without errors and tables exist."""
    stats = graph_store.get_graph_stats()
    assert stats["total_nodes"] == 0
    assert stats["total_relationships"] == 0
    assert stats["entity_breakdown"] == {}


def test_insert_and_get_entity(graph_store):
    """Verify inserting and fetching a single entity."""
    case_entity = LegalEntity.create(
        name="OA 83/2025",
        entity_type="CASE",
        properties={"status": "PENDING", "court": "NGT"}
    )
    graph_store.insert_entity(case_entity)

    fetched = graph_store.get_entity("case_oa_83_2025")
    assert fetched is not None
    assert fetched["id"] == "case_oa_83_2025"
    assert fetched["name"] == "OA 83/2025"
    assert fetched["entity_type"] == "CASE"
    assert fetched["properties"]["status"] == "PENDING"
    assert fetched["properties"]["court"] == "NGT"


def test_insert_and_traverse_relation(graph_store):
    """Verify relationship insertion and 1-hop neighbor traversal."""
    case = LegalEntity.create("OA 83/2025", "CASE")
    judge = LegalEntity.create("Justice Prakash Shrivastava", "JUDGE")
    counsel = LegalEntity.create("Adv. Sanjay Upadhyay", "COUNSEL")

    graph_store.insert_entity(case)
    graph_store.insert_entity(judge)
    graph_store.insert_entity(counsel)

    # Add relations
    graph_store.insert_relation(LegalRelation(
        source_id=case.id,
        relation_type="PRESIDED_BY",
        target_id=judge.id
    ))
    graph_store.insert_relation(LegalRelation(
        source_id=counsel.id,
        relation_type="REPRESENTS",
        target_id=case.id
    ))

    # Test neighbor traversal for Case (should have 1 outgoing to Judge and 1 incoming from Counsel)
    neighbors = graph_store.get_neighbors(case.id)
    assert len(neighbors) == 2

    neighbor_ids = {n["neighbor_id"] for n in neighbors}
    assert judge.id in neighbor_ids
    assert counsel.id in neighbor_ids

    # Test filtered by relation_type
    judge_neighbors = graph_store.get_neighbors(case.id, relation_type="PRESIDED_BY")
    assert len(judge_neighbors) == 1
    assert judge_neighbors[0]["neighbor_id"] == judge.id


def test_batch_graph_extraction_and_precedents(graph_store):
    """Verify batch insertion and 2-hop precedent discovery."""
    extraction = GraphExtraction(
        entities=[
            LegalEntity.create("OA 83/2025", "CASE"),
            LegalEntity.create("OA 100/2018 (Vardhaman Kaushik)", "CASE"),
            LegalEntity.create("NGT Act 2010 (Section 14)", "STATUTE"),
        ],
        relationships=[
            LegalRelation(
                source_id="case_oa_83_2025",
                relation_type="CITES_PRECEDENT",
                target_id="case_oa_100_2018_vardhaman_kaushik"
            ),
            LegalRelation(
                source_id="case_oa_100_2018_vardhaman_kaushik",
                relation_type="INVOKES_STATUTE",
                target_id="statute_ngt_act_2010_section_14"
            ),
        ]
    )
    graph_store.insert_graph_data(extraction)

    chains = graph_store.find_connected_precedents("case_oa_83_2025")
    assert len(chains) >= 1

    first_chain = chains[0]
    assert first_chain["target_id"] == "case_oa_100_2018_vardhaman_kaushik"
    assert first_chain["relation"] == "CITES_PRECEDENT"
    assert first_chain["sub_target_id"] == "statute_ngt_act_2010_section_14"
    assert first_chain["sub_relation"] == "INVOKES_STATUTE"


def test_queries_by_counsel_and_judge(graph_store):
    """Verify querying cases by counsel and presiding judge."""
    counsel = LegalEntity.create("Adv. Sanjay Upadhyay", "COUNSEL")
    judge = LegalEntity.create("Justice Prakash Shrivastava", "JUDGE")
    case1 = LegalEntity.create("OA 83/2025", "CASE")
    case2 = LegalEntity.create("OA 84/2025", "CASE")

    graph_store.insert_entity(counsel)
    graph_store.insert_entity(judge)
    graph_store.insert_entity(case1)
    graph_store.insert_entity(case2)

    graph_store.insert_relation(LegalRelation(source_id=counsel.id, relation_type="REPRESENTS", target_id=case1.id))
    graph_store.insert_relation(LegalRelation(source_id=case1.id, relation_type="PRESIDED_BY", target_id=judge.id))
    graph_store.insert_relation(LegalRelation(source_id=case2.id, relation_type="PRESIDED_BY", target_id=judge.id))

    # Query cases by counsel
    counsel_cases = graph_store.find_cases_by_counsel("Adv. Sanjay Upadhyay")
    assert len(counsel_cases) == 1
    assert counsel_cases[0]["id"] == case1.id

    # Query cases by judge
    judge_cases = graph_store.find_cases_by_judge("Justice Prakash Shrivastava")
    assert len(judge_cases) == 2
    judge_case_ids = {c["id"] for c in judge_cases}
    assert case1.id in judge_case_ids
    assert case2.id in judge_case_ids


def test_export_networkx_graph(graph_store):
    """Verify exporting Kùzu graph into NetworkX directed graph."""
    case = LegalEntity.create("OA 83/2025", "CASE")
    judge = LegalEntity.create("Justice PS", "JUDGE")
    graph_store.insert_entity(case)
    graph_store.insert_entity(judge)
    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="PRESIDED_BY", target_id=judge.id))

    nx_graph = graph_store.export_networkx_graph()
    assert isinstance(nx_graph, nx.DiGraph)
    assert nx_graph.number_of_nodes() == 2
    assert nx_graph.number_of_edges() == 1
    assert nx_graph.has_edge(case.id, judge.id)
    assert nx_graph.nodes[case.id]["name"] == "OA 83/2025"


def test_sync_from_sqlite(graph_store, tmp_path):
    """Verify syncing relational cases, counsels, and parties from SQLite."""
    sqlite_file = str(tmp_path / "test_lawnidhi.db")
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE cases (id INTEGER PRIMARY KEY, case_number TEXT, case_year TEXT, diary_number TEXT);
    """)
    cursor.execute("""
        CREATE TABLE counsels (id INTEGER PRIMARY KEY, name TEXT);
    """)
    cursor.execute("""
        CREATE TABLE case_counsels (case_id INTEGER, counsel_id INTEGER, PRIMARY KEY (case_id, counsel_id));
    """)
    cursor.execute("""
        CREATE TABLE parties (id INTEGER PRIMARY KEY, case_id INTEGER, name TEXT, role TEXT);
    """)

    cursor.execute("INSERT INTO cases VALUES (1, '83', '2025', '12345')")
    cursor.execute("INSERT INTO counsels VALUES (1, 'Adv. Sanjay Upadhyay')")
    cursor.execute("INSERT INTO case_counsels VALUES (1, 1)")
    cursor.execute("INSERT INTO parties VALUES (1, 1, 'DPCC', 'Respondent')")
    conn.commit()
    conn.close()

    count = graph_store.sync_from_sqlite(sqlite_file)
    assert count == 1

    stats = graph_store.get_graph_stats()
    assert stats["total_nodes"] == 3  # 1 Case, 1 Counsel, 1 Party
    assert stats["total_relationships"] == 2  # 1 REPRESENTS, 1 PARTY_TO
