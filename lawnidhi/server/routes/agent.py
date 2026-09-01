"""agent.py: FastAPI route handlers for Agentic Legal Co-Counsel and Case Briefing."""
from __future__ import annotations
from typing import Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.rag.vector_store import LegalDocumentStore
from lawnidhi.agent.co_counsel import AgenticCoCounsel
from lawnidhi.agent.schema import CoCounselResponse, CaseBrief
from lawnidhi.server.routes.graph import get_graph_store
from lawnidhi.server.routes.rag import get_doc_store

router = APIRouter(prefix="/api/agent", tags=["Agentic Legal Co-Counsel"])


class AgentChatRequest(BaseModel):
    query: str = Field(description="Legal instruction or complex research prompt")
    max_loops: int = Field(default=10, ge=1, le=15, description="Maximum ReAct loop iterations")


class CaseBriefRequest(BaseModel):
    case: str = Field(description="Case number or ID (e.g. '985/2019' or '83/2025')")


@router.post("/chat", response_model=CoCounselResponse, summary="Execute multi-step ReAct legal reasoning and research")
def chat_with_co_counsel(
    body: AgentChatRequest,
    graph_store: LegalGraphStore = Depends(get_graph_store),
    doc_store: LegalDocumentStore = Depends(get_doc_store)
) -> CoCounselResponse:
    agent = AgenticCoCounsel(
        graph_store=graph_store,
        doc_store=doc_store,
        max_loops=body.max_loops
    )
    return agent.run(body.query)


@router.post("/brief", response_model=CaseBrief, summary="Generate structured Case Brief for a matter")
def generate_case_brief(
    body: CaseBriefRequest,
    graph_store: LegalGraphStore = Depends(get_graph_store),
    doc_store: LegalDocumentStore = Depends(get_doc_store)
) -> CaseBrief:
    agent = AgenticCoCounsel(graph_store=graph_store, doc_store=doc_store)
    return agent.tools.generate_case_brief(body.case)
