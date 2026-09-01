"""test_server_api.py: Unit and integration tests for LawNidhi FastAPI REST Service."""
import os
import pytest
from fastapi.testclient import TestClient
from lawnidhi.server.app import create_app
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import LegalEntity, LegalRelation


@pytest.fixture
def client_with_test_db(tmp_path):
    db_path = str(tmp_path / "kuzu_api_test_db")
    store = LegalGraphStore(db_path=db_path)

    # Insert test data
    case = LegalEntity.create(name="OA 630/2023", entity_type="CASE", properties={"case_number": "630", "case_year": "2023"})
    hearing = LegalEntity.create(name="Hearing 2026-09-01", entity_type="HEARING", properties={"date": "2026-09-01", "court_no": "Court 1", "list_type": "Final"})
    judge = LegalEntity.create(name="Justice Prakash Shrivastava", entity_type="JUDGE")
    counsel = LegalEntity.create(name="Bhanwar Pal Singh", entity_type="COUNSEL")
    party = LegalEntity.create(name="Anand Arya", entity_type="PARTY", properties={"role": "Applicant"})
    precedent = LegalEntity.create(name="Vellore Citizens Welfare Forum (5 SCC 647)", entity_type="CASE", properties={"citation": "5 SCC 647"})
    statute = LegalEntity.create(name="Section 14, NGT Act 2010", entity_type="SECTION", properties={"section": "14", "act": "NGT Act 2010"})

    for e in [case, hearing, judge, counsel, party, precedent, statute]:
        store.insert_entity(e)

    store.insert_relation(LegalRelation(source_id=case.id, relation_type="LISTED_AT", target_id=hearing.id, properties={"item_number": 32}))
    store.insert_relation(LegalRelation(source_id=hearing.id, relation_type="PRESIDED_BY", target_id=judge.id))
    store.insert_relation(LegalRelation(source_id=counsel.id, relation_type="REPRESENTS", target_id=case.id))
    store.insert_relation(LegalRelation(source_id=counsel.id, relation_type="APPEARED_IN", target_id=hearing.id, properties={"case_id": case.id, "item_number": 32}))
    store.insert_relation(LegalRelation(source_id=party.id, relation_type="PARTY_TO", target_id=case.id))
    store.insert_relation(LegalRelation(source_id=case.id, relation_type="CITES_PRECEDENT", target_id=precedent.id))
    store.insert_relation(LegalRelation(source_id=case.id, relation_type="INVOKES_STATUTE", target_id=statute.id))
    store.close()

    app = create_app(db_path=db_path)
    with TestClient(app) as test_client:
        yield test_client


def test_root_and_health(client_with_test_db):
    res_root = client_with_test_db.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client_with_test_db.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_graph_stats_api(client_with_test_db):
    res = client_with_test_db.get("/api/graph/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_nodes"] >= 7
    assert data["total_relationships"] >= 7
    assert "CASE" in data["entity_breakdown"]


def test_daily_board_api(client_with_test_db):
    res = client_with_test_db.get("/api/graph/daily-board?date=2026-09-01")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] == 1
    assert data["cases"][0]["item_number"] == 32


def test_counsel_portfolio_api(client_with_test_db):
    res = client_with_test_db.get("/api/graph/counsel/Bhanwar%20Pal%20Singh/portfolio")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] == 1
    assert "Bhanwar Pal Singh" in data["counsel_name"]
    assert len(data["distinct_judges"]) == 1


def test_judge_caseload_api(client_with_test_db):
    res = client_with_test_db.get("/api/graph/judge/Prakash%20Shrivastava/caseload")
    assert res.status_code == 200
    data = res.json()
    assert data["total_hearings"] == 1
    assert data["total_cases"] == 1


def test_case_precedents_api(client_with_test_db):
    res = client_with_test_db.get("/api/graph/case/630/2023/precedents")
    assert res.status_code == 200
    data = res.json()
    assert data["total_precedents"] >= 2


def test_raw_cypher_query_api(client_with_test_db):
    payload = {"query": "MATCH (n:LegalEntity) RETURN n.entity_type, count(n)"}
    res = client_with_test_db.post("/api/graph/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["row_count"] >= 5


def test_export_graph_api(client_with_test_db):
    res = client_with_test_db.get("/api/graph/export?format=json")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
