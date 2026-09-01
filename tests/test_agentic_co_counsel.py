"""test_agentic_co_counsel.py: Unit tests for Phase 7 Agentic Legal Co-Counsel."""
import os
import pytest
from fastapi.testclient import TestClient

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import LegalEntity, LegalRelation
from lawnidhi.rag.vector_store import LegalDocumentStore
from lawnidhi.agent.schema import AgentStep, CoCounselResponse, CaseBrief
from lawnidhi.agent.tools import LegalToolRegistry
from lawnidhi.agent.co_counsel import AgenticCoCounsel
from lawnidhi.server.app import create_app


@pytest.fixture
def agent_test_environment(tmp_path):
    db_path = str(tmp_path / "kuzu_agent_test_db")
    graph_store = LegalGraphStore(db_path=db_path)

    # Insert test entities
    case = LegalEntity.create(name="Original Application No. 985/2019", entity_type="CASE")
    counsel = LegalEntity.create(name="Bhanwar Pal Singh", entity_type="COUNSEL")
    statute = LegalEntity.create(name="Section 25, Water (Prevention and Control of Pollution) Act, 1974", entity_type="SECTION")
    judge = LegalEntity.create(name="Justice Prakash Shrivastava", entity_type="JUDGE")
    precedent = LegalEntity.create(name="Vellore Citizens Welfare Forum v. UOI (1996) 5 SCC 647", entity_type="CASE")

    for e in [case, counsel, statute, judge, precedent]:
        graph_store.insert_entity(e)

    # Interconnect
    graph_store.insert_relation(LegalRelation(source_id=counsel.id, relation_type="REPRESENTS", target_id=case.id))
    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="INVOKES_STATUTE", target_id=statute.id))
    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="CITES_PRECEDENT", target_id=precedent.id))
    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="DELIVERED_BY", target_id=judge.id))

    # Doc store
    doc_store = LegalDocumentStore()
    doc_store.add_document(
        doc_id="OA_985_2019",
        case_name="OA 985/2019",
        text="The National Green Tribunal directed strict compliance with Section 25 of Water Act 1974 regarding industrial effluents.",
        order_date="2026-03-25"
    )

    yield graph_store, doc_store, db_path

    graph_store.close()


def test_legal_tool_registry(agent_test_environment):
    graph_store, doc_store, _ = agent_test_environment
    tools = LegalToolRegistry(graph_store=graph_store, doc_store=doc_store)

    # 1. query_graph
    cy_res = tools.query_graph("MATCH (c:LegalEntity) RETURN count(c) AS cnt")
    assert cy_res["row_count"] >= 1

    # 2. get_precedents
    prec_res = tools.get_precedents("985/2019")
    assert prec_res["total_precedents"] >= 1

    # 3. check_counsel
    c_res = tools.check_counsel("Bhanwar Pal Singh")
    assert c_res["counsel"] == "Bhanwar Pal Singh"
    assert c_res["portfolio_total_cases"] >= 1

    # 4. generate_case_brief
    brief = tools.generate_case_brief("985/2019")
    assert isinstance(brief, CaseBrief)
    assert len(brief.invoked_statutes) >= 1
    assert len(brief.cited_precedents) >= 1


def test_agentic_co_counsel_react_loop(agent_test_environment):
    graph_store, doc_store, _ = agent_test_environment
    agent = AgenticCoCounsel(graph_store=graph_store, doc_store=doc_store, max_loops=10)

    # 1. Case Brief Query
    res_brief = agent.run("Prepare a case brief for OA 985/2019")
    assert isinstance(res_brief, CoCounselResponse)
    assert res_brief.loop_count <= 10
    assert "generate_case_brief" in res_brief.tools_invoked
    assert "Section 25" in res_brief.final_answer

    # 2. Counsel Appearance Query
    res_counsel = agent.run("Check court appearances and clashes for advocate Bhanwar Pal Singh")
    assert isinstance(res_counsel, CoCounselResponse)
    assert "check_counsel" in res_counsel.tools_invoked
    assert "Bhanwar Pal Singh" in res_counsel.final_answer

    # 3. Judge Caseload Query
    res_judge = agent.run("What cases are heard by Justice Prakash Shrivastava?")
    assert isinstance(res_judge, CoCounselResponse)
    assert "get_judge_caseload" in res_judge.tools_invoked


def test_agent_api_endpoints(agent_test_environment):
    _, _, db_path = agent_test_environment
    app = create_app(db_path=db_path)

    with TestClient(app) as client:
        # 1. POST /api/agent/chat
        res_chat = client.post("/api/agent/chat", json={
            "query": "Prepare a case brief for OA 985/2019",
            "max_loops": 10
        })
        assert res_chat.status_code == 200
        data_chat = res_chat.json()
        assert "Case Brief" in data_chat["final_answer"]
        assert len(data_chat["steps"]) >= 2

        # 2. POST /api/agent/brief
        res_brief = client.post("/api/agent/brief", json={"case": "985/2019"})
        assert res_brief.status_code == 200
        data_brief = res_brief.json()
        assert len(data_brief["invoked_statutes"]) >= 1
