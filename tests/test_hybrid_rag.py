"""test_hybrid_rag.py: Unit and integration tests for Phase 5 Hybrid GraphRAG Retriever."""
import os
import pytest
from fastapi.testclient import TestClient

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import LegalEntity, LegalRelation
from lawnidhi.rag.vector_store import LegalDocumentStore
from lawnidhi.rag.graph_expander import GraphContextExpander
from lawnidhi.rag.hybrid_retriever import HybridGraphRAGRetriever
from lawnidhi.rag.synthesizer import LegalSynthesizer
from lawnidhi.server.app import create_app


@pytest.fixture
def rag_test_environment(tmp_path):
    db_path = str(tmp_path / "kuzu_rag_test_db")
    graph_store = LegalGraphStore(db_path=db_path)

    # Insert graph entities
    case = LegalEntity.create(name="Original Application No. 985/2019", entity_type="CASE", properties={"case_number": "985", "case_year": "2019"})
    statute = LegalEntity.create(name="Section 25, Water (Prevention and Control of Pollution) Act, 1974", entity_type="SECTION")
    precedent = LegalEntity.create(name="Vellore Citizens Welfare Forum v. UOI (5 SCC 647)", entity_type="CASE")
    judge = LegalEntity.create(name="Justice Adarsh Kumar Goel", entity_type="JUDGE")

    for e in [case, statute, precedent, judge]:
        graph_store.insert_entity(e)

    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="INVOKES_STATUTE", target_id=statute.id))
    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="CITES_PRECEDENT", target_id=precedent.id))
    graph_store.insert_relation(LegalRelation(source_id=case.id, relation_type="DELIVERED_BY", target_id=judge.id))

    # Setup document store
    doc_store = LegalDocumentStore(chunk_size=300, chunk_overlap=50)
    sample_text = (
        "The applicant alleged untreated discharge of industrial trade effluents into the river. "
        "The Tribunal examined violations under Section 25 of the Water Act 1974. "
        "Relying on the precautionary principle in Vellore Citizens Welfare Forum (1996) 5 SCC 647, "
        "an environmental compensation of Rs 10 Crores was imposed."
    )
    doc_store.add_document(
        doc_id="070110900591-2019_15-11-2019_order",
        case_name="Original Application No. 985/2019",
        text=sample_text,
        order_date="2019-11-15",
        court_number="Court 1"
    )
    doc_store.build_index()

    yield graph_store, doc_store, db_path

    graph_store.close()


def test_document_store_search(rag_test_environment):
    _, doc_store, _ = rag_test_environment
    results = doc_store.search("industrial trade effluents Water Act", top_k=2)
    assert len(results) >= 1
    assert "985/2019" in results[0].case_name
    assert results[0].score > 0.0


def test_graph_expander(rag_test_environment):
    graph_store, _, _ = rag_test_environment
    expander = GraphContextExpander(graph_store)

    nodes, statutes, precedents, judges = expander.expand_cases(["985/2019"])
    assert len(statutes) >= 1
    assert any("Water" in s for s in statutes)
    assert len(precedents) >= 1
    assert any("Vellore" in p for p in precedents)
    assert len(judges) >= 1


def test_hybrid_retriever_pipeline(rag_test_environment):
    graph_store, doc_store, _ = rag_test_environment
    retriever = HybridGraphRAGRetriever(doc_store=doc_store, graph_store=graph_store)

    result = retriever.retrieve("What are the penalties under Section 25 of Water Act for effluent discharge?")
    assert len(result.text_chunks) >= 1
    assert len(result.statutory_provisions) >= 1
    assert len(result.precedent_lineage) >= 1
    assert "Section 25" in result.formatted_context
    assert "Vellore Citizens" in result.formatted_context


def test_legal_synthesizer_deterministic(rag_test_environment):
    graph_store, doc_store, _ = rag_test_environment
    retriever = HybridGraphRAGRetriever(doc_store=doc_store, graph_store=graph_store)
    result = retriever.retrieve("effluent discharge Water Act")

    synthesizer = LegalSynthesizer()
    answer = synthesizer.synthesize(result)

    assert "Legal Summary" in answer.answer
    assert len(answer.cited_statutes) >= 1
    assert len(answer.cited_precedents) >= 1
    assert answer.retrieval_metadata["mode"] == "deterministic_grounded"


def test_fastapi_rag_endpoints(rag_test_environment):
    _, doc_store, db_path = rag_test_environment
    app = create_app(db_path=db_path)
    app.state.doc_store = doc_store

    with TestClient(app) as client:
        # Test /api/rag/retrieve
        res_ret = client.post("/api/rag/retrieve", json={"query": "Water Act effluent penalty", "top_k": 3})
        assert res_ret.status_code == 200
        data_ret = res_ret.json()
        assert len(data_ret["text_chunks"]) >= 1
        assert len(data_ret["statutory_provisions"]) >= 1

        # Test /api/rag/ask
        res_ask = client.post("/api/rag/ask", json={"query": "Water Act effluent penalty", "top_k": 3})
        assert res_ask.status_code == 200
        data_ask = res_ask.json()
        assert "Legal Summary" in data_ask["answer"]
        assert len(data_ask["cited_statutes"]) >= 1
