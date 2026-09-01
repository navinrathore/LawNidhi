import os
import pytest
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import LegalEntity, LegalRelation

@pytest.fixture
def graph_store(tmp_path):
    db_path = str(tmp_path / "kuzu_test_db")
    store = LegalGraphStore(db_path=db_path)
    
    # Insert test data: Case, Hearing, Judge, Counsel, Party, Precedent, Statute
    case = LegalEntity.create(name="OA 630/2023", entity_type="CASE", properties={"case_number": "630", "case_year": "2023"})
    hearing = LegalEntity.create(name="Hearing 2026-09-01", entity_type="HEARING", properties={"date": "2026-09-01", "court_no": "Court 1", "list_type": "Final"})
    judge = LegalEntity.create(name="Justice Prakash Shrivastava", entity_type="JUDGE")
    counsel = LegalEntity.create(name="Bhanwar Pal Singh", entity_type="COUNSEL")
    party = LegalEntity.create(name="Anand Arya", entity_type="PARTY", properties={"role": "Applicant"})
    precedent = LegalEntity.create(name="Vellore Citizens Welfare Forum (1996) 5 SCC 647", entity_type="CASE")
    statute = LegalEntity.create(name="Section 14, NGT Act 2010", entity_type="STATUTE")

    for e in [case, hearing, judge, counsel, party, precedent, statute]:
        store.insert_entity(e)

    # Relations
    store.insert_relation(LegalRelation(source_id=case.id, relation_type="LISTED_AT", target_id=hearing.id, properties={"item_number": 32}))
    store.insert_relation(LegalRelation(source_id=hearing.id, relation_type="PRESIDED_BY", target_id=judge.id))
    store.insert_relation(LegalRelation(source_id=counsel.id, relation_type="REPRESENTS", target_id=case.id))
    store.insert_relation(LegalRelation(source_id=counsel.id, relation_type="APPEARED_IN", target_id=hearing.id, properties={"case_id": case.id, "item_number": 32}))
    store.insert_relation(LegalRelation(source_id=party.id, relation_type="PARTY_TO", target_id=case.id))
    store.insert_relation(LegalRelation(source_id=case.id, relation_type="CITES_PRECEDENT", target_id=precedent.id))
    store.insert_relation(LegalRelation(source_id=case.id, relation_type="INVOKES_STATUTE", target_id=statute.id))

    yield store
    store.close()

def test_resolve_case_id(graph_store):
    case_id = graph_store.resolve_case_id("630/2023")
    assert case_id is not None
    assert "630" in case_id

def test_get_counsel_portfolio(graph_store):
    portfolio = graph_store.get_counsel_portfolio("Bhanwar Pal Singh")
    assert portfolio["total_cases"] == 1
    assert "Bhanwar Pal Singh" in portfolio["counsel_name"]
    assert len(portfolio["distinct_judges"]) == 1
    assert "Justice Prakash Shrivastava" in portfolio["distinct_judges"][0]
    assert "Anand Arya" in portfolio["distinct_parties"]

def test_get_judge_caseload(graph_store):
    caseload = graph_store.get_judge_caseload("Prakash Shrivastava")
    assert caseload["total_hearings"] == 1
    assert caseload["total_cases"] == 1
    assert len(caseload["hearings"]) == 1

def test_execute_raw_cypher(graph_store):
    res = graph_store.execute_raw_cypher("MATCH (n:LegalEntity) RETURN n.entity_type, count(n)")
    assert res["row_count"] > 0
    assert len(res["rows"]) >= 5

def test_export_graph_format_json(graph_store):
    json_export = graph_store.export_graph_format("json")
    assert "nodes" in json_export
    assert "links" in json_export

def test_export_graph_format_dot(graph_store):
    dot_export = graph_store.export_graph_format("dot")
    assert "digraph" in dot_export
    assert "CITES_PRECEDENT" in dot_export

def test_find_connected_precedents(graph_store):
    precedents = graph_store.find_connected_precedents("630/2023")
    assert len(precedents) == 2
    relations = [p["relation"] for p in precedents]
    assert "CITES_PRECEDENT" in relations
    assert "INVOKES_STATUTE" in relations
