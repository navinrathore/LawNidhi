"""graph_expander.py: Multi-hop Knowledge Graph subgraph expansion for Hybrid GraphRAG."""
from __future__ import annotations
import re
from typing import Dict, List, Set, Tuple, Any
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.rag.schema import GraphContextNode


class GraphContextExpander:
    """Expands candidate cases and query tokens into connected Knowledge Graph subgraphs."""

    def __init__(self, store: LegalGraphStore):
        self.store = store

    def expand_cases(self, case_identifiers: List[str]) -> Tuple[List[GraphContextNode], List[str], List[str], List[str]]:
        """Traverse 1-to-2 hop subgraphs for a list of case IDs or case number strings.
        
        Returns:
            - graph_nodes: Structured GraphContextNode models
            - statutory_provisions: Clean list of distinct sections/acts
            - precedent_lineage: Clean list of cited landmark cases
            - bench_judges: Clean list of presiding judges
        """
        graph_nodes: List[GraphContextNode] = []
        statutory_provisions: Set[str] = set()
        precedent_lineage: Set[str] = set()
        bench_judges: Set[str] = set()
        seen_edges: Set[Tuple[str, str, str]] = set()

        for case_ref in case_identifiers:
            case_id = self.store.resolve_case_id(case_ref) or case_ref
            
            # Query outgoing relationships from case (Statutes, Precedents, Judges)
            cypher = """
            MATCH (c:LegalEntity)-[r:RelatesTo]->(target:LegalEntity)
            WHERE c.id = $cid OR c.name CONTAINS $raw
            RETURN c.id, c.name, r.relation_type, target.id, target.name, target.entity_type, r.properties
            LIMIT 50
            """
            try:
                res = self.store.conn.execute(cypher, {"cid": case_id, "raw": case_ref})
                while res.has_next():
                    row = res.get_next()
                    src_id, src_name, rel_type, tgt_id, tgt_name, tgt_type, props = row
                    
                    edge_key = (src_id, rel_type, tgt_id)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        node = GraphContextNode(
                            id=tgt_id,
                            name=tgt_name,
                            entity_type=tgt_type,
                            relation=rel_type,
                            connected_to=src_name or src_id,
                            properties=props if isinstance(props, dict) else {}
                        )
                        graph_nodes.append(node)

                        if rel_type == "INVOKES_STATUTE" or tgt_type == "SECTION":
                            statutory_provisions.add(tgt_name)
                        elif rel_type == "CITES_PRECEDENT":
                            precedent_lineage.add(tgt_name)
                        elif rel_type == "DELIVERED_BY" or tgt_type == "JUDGE":
                            bench_judges.add(tgt_name)
            except Exception:
                continue

        return (
            graph_nodes,
            sorted(list(statutory_provisions)),
            sorted(list(precedent_lineage)),
            sorted(list(bench_judges))
        )

    def expand_by_keywords(self, query: str) -> Tuple[List[GraphContextNode], List[str], List[str], List[str]]:
        """Identify statutory sections, act names, or judges directly mentioned in query and expand their graph neighbors."""
        graph_nodes: List[GraphContextNode] = []
        statutory_provisions: Set[str] = set()
        precedent_lineage: Set[str] = set()
        bench_judges: Set[str] = set()

        # Check for section mentions (e.g. "Section 25" or "Section 14")
        sec_matches = re.findall(r"(?i)\b(?:section|sec\.?)\s+([0-9]+[A-Za-z]*)", query)
        for sec in sec_matches:
            cypher = """
            MATCH (s:LegalEntity {entity_type: 'SECTION'})<-[r:RelatesTo]-(c:LegalEntity)
            WHERE s.id CONTAINS $sec OR s.name CONTAINS $sec
            RETURN c.id, c.name, r.relation_type, s.id, s.name, s.entity_type
            LIMIT 10
            """
            try:
                res = self.store.conn.execute(cypher, {"sec": sec.lower()})
                while res.has_next():
                    c_id, c_name, rel, s_id, s_name, s_type = res.get_next()
                    statutory_provisions.add(s_name)
                    graph_nodes.append(GraphContextNode(
                        id=s_id,
                        name=s_name,
                        entity_type=s_type,
                        relation=rel,
                        connected_to=c_name
                    ))
            except Exception:
                continue

        return (
            graph_nodes,
            sorted(list(statutory_provisions)),
            sorted(list(precedent_lineage)),
            sorted(list(bench_judges))
        )
