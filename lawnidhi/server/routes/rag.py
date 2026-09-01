"""rag.py: FastAPI route handlers for Hybrid GraphRAG and Legal Question Answering."""
from __future__ import annotations
import os
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.rag.vector_store import LegalDocumentStore
from lawnidhi.rag.hybrid_retriever import HybridGraphRAGRetriever
from lawnidhi.rag.synthesizer import LegalSynthesizer
from lawnidhi.rag.schema import HybridRetrievalResult, RAGAnswer
from lawnidhi.server.routes.graph import get_graph_store

router = APIRouter(prefix="/api/rag", tags=["Hybrid GraphRAG"])


class RAGQueryRequest(BaseModel):
    query: str = Field(description="Legal question or query string (e.g. 'Water Act Section 25 industrial effluent penalties')")
    top_k: int = Field(default=5, description="Number of text chunks to retrieve")


def get_doc_store(request: Request) -> LegalDocumentStore:
    """Dependency provider for shared LegalDocumentStore singleton."""
    doc_store = getattr(request.app.state, "doc_store", None)
    if doc_store is None:
        doc_store = LegalDocumentStore()
        orders_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "orders")
        if os.path.isdir(orders_dir):
            doc_store.index_directory(orders_dir)
        request.app.state.doc_store = doc_store
    return doc_store


@router.post("/retrieve", response_model=HybridRetrievalResult, summary="Retrieve hybrid text passages and Knowledge Graph subgraph context")
def retrieve_hybrid_context(
    body: RAGQueryRequest,
    graph_store: LegalGraphStore = Depends(get_graph_store),
    doc_store: LegalDocumentStore = Depends(get_doc_store)
) -> HybridRetrievalResult:
    retriever = HybridGraphRAGRetriever(doc_store=doc_store, graph_store=graph_store)
    return retriever.retrieve(query=body.query, top_k=body.top_k)


@router.post("/ask", response_model=RAGAnswer, summary="Ask a legal question and receive a grounded RAG synthesis")
def ask_question(
    body: RAGQueryRequest,
    graph_store: LegalGraphStore = Depends(get_graph_store),
    doc_store: LegalDocumentStore = Depends(get_doc_store)
) -> RAGAnswer:
    retriever = HybridGraphRAGRetriever(doc_store=doc_store, graph_store=graph_store)
    retrieval_res = retriever.retrieve(query=body.query, top_k=body.top_k)
    synthesizer = LegalSynthesizer()
    return synthesizer.synthesize(retrieval_res)
