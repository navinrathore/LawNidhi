"""tools.py: Deterministic Tool Registry for LawNidhi Agentic Co-Counsel (Rule 11)."""
from __future__ import annotations
import os
import re
from typing import Dict, List, Optional, Any
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.rag.vector_store import LegalDocumentStore
from lawnidhi.rag.hybrid_retriever import HybridGraphRAGRetriever
from lawnidhi.agent.schema import CaseBrief


class LegalToolRegistry:
    """Deterministic, 100% testable legal tools callable by the ReAct agent."""

    def __init__(self, graph_store: LegalGraphStore, doc_store: Optional[LegalDocumentStore] = None):
        self.graph_store = graph_store
        if doc_store is None:
            doc_store = LegalDocumentStore()
            orders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "orders")
            if os.path.isdir(orders_dir):
                doc_store.index_directory(orders_dir)
        self.doc_store = doc_store
        self.retriever = HybridGraphRAGRetriever(doc_store=self.doc_store, graph_store=self.graph_store)

    def query_graph(self, cypher: str) -> Dict[str, Any]:
        """Execute a raw openCypher query on the Kùzu Knowledge Graph."""
        try:
            return self.graph_store.execute_raw_cypher(cypher)
        except Exception as e:
            return {"error": str(e), "query": cypher, "row_count": 0, "rows": []}

    def get_precedents(self, case_id_or_number: str) -> Dict[str, Any]:
        """Retrieve multi-hop precedent citations and statutory sections for a case."""
        precedents = self.graph_store.find_connected_precedents(case_id_or_number)
        return {
            "case": case_id_or_number,
            "total_precedents": len(precedents),
            "precedents": precedents
        }

    def retrieve_hybrid_rag(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Retrieve hybrid text passages and Knowledge Graph context for a query."""
        res = self.retriever.retrieve(query, top_k=top_k)
        return {
            "query": query,
            "statutes": res.statutory_provisions,
            "precedents": res.precedent_lineage,
            "bench_judges": res.bench_judges,
            "chunks": [c.model_dump() for c in res.text_chunks],
            "context_text": res.formatted_context
        }

    def check_counsel(self, counsel_name: str, date: str = "today") -> Dict[str, Any]:
        """Check scheduled cases, portfolio, and detect courtroom clashes for an advocate."""
        portfolio = self.graph_store.get_counsel_portfolio(counsel_name)
        clashes = self.graph_store.find_counsel_clashes(date, counsel_name)
        return {
            "counsel": counsel_name,
            "date": date,
            "portfolio_total_cases": portfolio.get("total_cases", 0),
            "portfolio_judges": portfolio.get("distinct_judges", []),
            "portfolio_parties": portfolio.get("distinct_parties", []),
            "has_clashes": len(clashes) > 1,
            "clashes": clashes
        }

    def get_judge_caseload(self, judge_name: str) -> Dict[str, Any]:
        """Retrieve bench presiding caseload, hearing dates, and cases heard."""
        return self.graph_store.get_judge_caseload(judge_name)

    def generate_case_brief(self, case_id_or_number: str) -> CaseBrief:
        """Assemble an authoritative, complete Case Brief from Knowledge Graph & Order Text."""
        case_id = self.graph_store.resolve_case_id(case_id_or_number) or case_id_or_number
        timeline = self.graph_store.get_case_listing_history(case_id)
        precedents_data = self.graph_store.find_connected_precedents(case_id)

        statutes = [p["target_name"] for p in precedents_data if p["relation"] == "INVOKES_STATUTE" or p["target_type"] == "SECTION"]
        precedents = [p["target_name"] for p in precedents_data if p["relation"] == "CITES_PRECEDENT"]

        # Pull coram judges & parties via Cypher
        coram = []
        parties = []
        counsels = []
        try:
            res = self.graph_store.conn.execute(
                "MATCH (c:LegalEntity)-[r:RelatesTo]->(target:LegalEntity) WHERE c.id = $cid RETURN r.relation_type, target.name, target.entity_type",
                {"cid": case_id}
            )
            while res.has_next():
                rel, tname, ttype = res.get_next()
                if rel in ("DELIVERED_BY", "PRESIDED_BY") or ttype == "JUDGE":
                    if tname not in coram:
                        coram.append(tname)
                elif rel == "PARTY_TO" or ttype == "PARTY":
                    if tname not in parties:
                        parties.append(tname)
                elif rel in ("REPRESENTS", "APPEARED_IN") or ttype == "COUNSEL":
                    if tname not in counsels:
                        counsels.append(tname)
        except Exception:
            pass

        # Pull text excerpts
        rag_res = self.retriever.retrieve(case_id_or_number, top_k=2)
        findings = rag_res.text_chunks[0].text[:400] if rag_res.text_chunks else "No raw text excerpt found in order store."

        return CaseBrief(
            case_id=case_id,
            case_name=f"Case {case_id_or_number}",
            presiding_coram=coram,
            applicants=parties[:3],
            respondents=parties[3:6],
            counsels=counsels[:6],
            invoked_statutes=statutes,
            cited_precedents=precedents,
            case_timeline=timeline,
            key_findings=findings
        )
