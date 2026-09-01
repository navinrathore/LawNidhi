"""test_clustering_and_ui.py: Unit tests for Phase 6 Hierarchical Graph Summarization & Web UI."""
import os
import pytest
from fastapi.testclient import TestClient

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import LegalEntity, LegalRelation
from lawnidhi.graph.clustering import GraphClusterEngine
from lawnidhi.server.app import create_app


@pytest.fixture
def cluster_test_environment(tmp_path):
    db_path = str(tmp_path / "kuzu_cluster_test_db")
    graph_store = LegalGraphStore(db_path=db_path)

    # Build 2 distinct communities
    # Cluster 1: Water Act cluster
    case1 = LegalEntity.create(name="OA 985/2019", entity_type="CASE")
    counsel1 = LegalEntity.create(name="Raj Panjwani", entity_type="COUNSEL")
    statute1 = LegalEntity.create(name="Section 25, Water Act 1974", entity_type="SECTION")
    judge1 = LegalEntity.create(name="Justice Adarsh Goel", entity_type="JUDGE")

    # Cluster 2: NGT Act cluster
    case2 = LegalEntity.create(name="OA 83/2025", entity_type="CASE")
    counsel2 = LegalEntity.create(name="Bhanwar Pal Singh", entity_type="COUNSEL")
    statute2 = LegalEntity.create(name="Section 14, NGT Act 2010", entity_type="SECTION")
    judge2 = LegalEntity.create(name="Justice Prakash Shrivastava", entity_type="JUDGE")

    for e in [case1, counsel1, statute1, judge1, case2, counsel2, statute2, judge2]:
        graph_store.insert_entity(e)

    # Interconnect cluster 1
    graph_store.insert_relation(LegalRelation(source_id=counsel1.id, relation_type="REPRESENTS", target_id=case1.id))
    graph_store.insert_relation(LegalRelation(source_id=case1.id, relation_type="INVOKES_STATUTE", target_id=statute1.id))
    graph_store.insert_relation(LegalRelation(source_id=case1.id, relation_type="DELIVERED_BY", target_id=judge1.id))

    # Interconnect cluster 2
    graph_store.insert_relation(LegalRelation(source_id=counsel2.id, relation_type="REPRESENTS", target_id=case2.id))
    graph_store.insert_relation(LegalRelation(source_id=case2.id, relation_type="INVOKES_STATUTE", target_id=statute2.id))
    graph_store.insert_relation(LegalRelation(source_id=case2.id, relation_type="DELIVERED_BY", target_id=judge2.id))

    yield graph_store, db_path

    graph_store.close()


def test_cluster_engine_detects_communities(cluster_test_environment):
    graph_store, _ = cluster_test_environment
    engine = GraphClusterEngine(graph_store)

    summary = engine.detect_communities(min_size=2)
    assert summary.total_nodes >= 8
    assert summary.total_communities >= 2
    assert len(summary.communities) >= 2

    c1 = summary.communities[0]
    assert c1.size >= 3
    assert len(c1.top_hubs) >= 1


def test_fastapi_communities_endpoint(cluster_test_environment):
    _, db_path = cluster_test_environment
    app = create_app(db_path=db_path)

    with TestClient(app) as client:
        res = client.get("/api/graph/communities?min_size=2")
        assert res.status_code == 200
        data = res.json()
        assert data["total_communities"] >= 2
        assert len(data["communities"]) >= 2


def test_fastapi_web_ui_serving(cluster_test_environment):
    _, db_path = cluster_test_environment
    app = create_app(db_path=db_path)

    with TestClient(app) as client:
        # Test UI route
        res_ui = client.get("/ui")
        assert res_ui.status_code == 200
        assert "text/html" in res_ui.headers["content-type"]
        assert "LawNidhi" in res_ui.text

        # Test Static index.html
        res_static = client.get("/static/index.html")
        assert res_static.status_code == 200
        assert "Interactive Knowledge Graph Canvas" in res_static.text

        # Test Static index.css
        res_css = client.get("/static/index.css")
        assert res_css.status_code == 200
        assert "--bg-base" in res_css.text

        # Test Static app.js
        res_js = client.get("/static/app.js")
        assert res_js.status_code == 200
        assert "cytoscape" in res_js.text
