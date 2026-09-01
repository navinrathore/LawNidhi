"""hybrid_retriever.py: Hybrid GraphRAG retriever combining vector text chunks with multi-hop graph subgraphs."""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.rag.vector_store import LegalDocumentStore
from lawnidhi.rag.graph_expander import GraphContextExpander
from lawnidhi.rag.schema import HybridRetrievalResult, TextChunk, GraphContextNode


class HybridGraphRAGRetriever:
    """Combines semantic passage search with Knowledge Graph multi-hop entity traversal."""

    def __init__(self, doc_store: LegalDocumentStore, graph_store: LegalGraphStore):
        self.doc_store = doc_store
        self.graph_store = graph_store
        self.expander = GraphContextExpander(graph_store)

    def retrieve(self, query: str, top_k: int = 5) -> HybridRetrievalResult:
        """Execute parallel semantic retrieval + graph traversal and assemble grounded context."""
        # 1. Semantic vector search over text chunks
        text_chunks = self.doc_store.search(query, top_k=top_k)

        # 2. Extract candidate cases from chunks & query
        candidate_cases = set()
        for chunk in text_chunks:
            if chunk.case_name:
                candidate_cases.add(chunk.case_name)
            if chunk.doc_id:
                candidate_cases.add(chunk.doc_id)

        # Also check if query directly mentions case numbers (e.g. "985/2019" or "83/2025")
        import re
        case_nums = re.findall(r"\b\d+\/\d{4}\b", query)
        for num in case_nums:
            candidate_cases.add(num)

        # 3. Multi-hop Knowledge Graph expansion
        graph_nodes, statutes, precedents, judges = self.expander.expand_cases(list(candidate_cases))
        kw_nodes, kw_statutes, kw_precedents, kw_judges = self.expander.expand_by_keywords(query)

        # Merge and deduplicate
        all_nodes = graph_nodes + kw_nodes
        all_statutes = sorted(list(set(statutes + kw_statutes)))
        all_precedents = sorted(list(set(precedents + kw_precedents)))
        all_judges = sorted(list(set(judges + kw_judges)))

        # 4. Assemble clean markdown-grounded context
        context_str = self._format_grounded_context(
            query=query,
            chunks=text_chunks,
            statutes=all_statutes,
            precedents=all_precedents,
            judges=all_judges
        )

        return HybridRetrievalResult(
            query=query,
            text_chunks=text_chunks,
            graph_nodes=all_nodes,
            statutory_provisions=all_statutes,
            precedent_lineage=all_precedents,
            bench_judges=all_judges,
            formatted_context=context_str
        )

    def _format_grounded_context(
        self,
        query: str,
        chunks: List[TextChunk],
        statutes: List[str],
        precedents: List[str],
        judges: List[str]
    ) -> str:
        """Generate structured markdown context with explicit legal provenance."""
        lines = [f"# Grounded Legal Context for Query: '{query}'\n"]

        if statutes:
            lines.append("## 📜 Statutory Provisions Invoked (From Knowledge Graph):")
            for s in statutes:
                lines.append(f"  • {s}")
            lines.append("")

        if precedents:
            lines.append("## 🏛️ Binding Precedent Citations (From Knowledge Graph):")
            for p in precedents:
                lines.append(f"  • {p}")
            lines.append("")

        if judges:
            lines.append("## ⚖️ Bench Members / Coram (From Knowledge Graph):")
            for j in judges:
                lines.append(f"  • {j}")
            lines.append("")

        if chunks:
            lines.append("## 📄 Relevant Judicial Order Text Excerpts:")
            for i, c in enumerate(chunks, start=1):
                date_str = f" | Date: {c.order_date}" if c.order_date else ""
                lines.append(f"### [Source {i}] {c.case_name}{date_str} (Score: {c.score:.4f})")
                lines.append(f"> \"{c.text}\"\n")

        return "\n".join(lines)
