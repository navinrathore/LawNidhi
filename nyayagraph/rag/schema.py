"""schema.py: Pydantic schemas for Hybrid GraphRAG Retrieval and Context Synthesis."""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TextChunk(BaseModel):
    chunk_id: str
    doc_id: str
    case_name: str
    order_date: Optional[str] = None
    court_number: Optional[str] = None
    text: str
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphContextNode(BaseModel):
    id: str
    name: str
    entity_type: str
    relation: str
    connected_to: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class HybridRetrievalResult(BaseModel):
    query: str
    text_chunks: List[TextChunk] = Field(default_factory=list)
    graph_nodes: List[GraphContextNode] = Field(default_factory=list)
    statutory_provisions: List[str] = Field(default_factory=list)
    precedent_lineage: List[str] = Field(default_factory=list)
    bench_judges: List[str] = Field(default_factory=list)
    formatted_context: str = ""


class RAGAnswer(BaseModel):
    query: str
    answer: str
    source_cases: List[str] = Field(default_factory=list)
    cited_statutes: List[str] = Field(default_factory=list)
    cited_precedents: List[str] = Field(default_factory=list)
    bench_members: List[str] = Field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
