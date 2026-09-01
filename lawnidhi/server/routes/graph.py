"""graph.py: FastAPI route handlers for Knowledge Graph operations."""
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from lawnidhi.graph.store import LegalGraphStore

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])


def get_graph_store(request: Request) -> LegalGraphStore:
    """Dependency provider for shared LegalGraphStore singleton."""
    store = getattr(request.app.state, "graph_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Knowledge Graph store is not initialized")
    return store


class CypherQueryRequest(BaseModel):
    query: str = Field(description="Raw openCypher query string (e.g. 'MATCH (n:LegalEntity) RETURN n LIMIT 10')")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameterized query arguments")


class CypherQueryResponse(BaseModel):
    query: str
    row_count: int
    rows: List[List[Any]]


@router.get("/stats", summary="Get Knowledge Graph statistics and node/edge breakdown")
def get_stats(store: LegalGraphStore = Depends(get_graph_store)) -> Dict[str, Any]:
    return store.get_graph_stats()


@router.get("/daily-board", summary="Get courtroom cause list board for a specific date")
def get_daily_board(
    date_str: str = Query("today", alias="date", description="Hearing date ('today', 'tomorrow', or YYYY-MM-DD)"),
    court: Optional[str] = Query(None, description="Optional court filter (e.g. 'Court 1')"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    clean_date = date_str.lower().strip()
    if clean_date == "today":
        target_date = date.today().isoformat()
    elif clean_date == "tomorrow":
        target_date = (date.today() + timedelta(days=1)).isoformat()
    else:
        target_date = date_str

    cases = store.get_cases_listed_on_date(target_date, court_no=court)
    return {
        "date": target_date,
        "court_filter": court,
        "total_cases": len(cases),
        "cases": cases
    }


@router.get("/counsel/{name}/cases", summary="Get scheduled cases for a counsel across dates")
def get_counsel_cases(
    name: str,
    start: str = Query("today", description="Start date ('today' or YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Optional end date (YYYY-MM-DD)"),
    days: int = Query(2, description="Number of days to search if end date is not given"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    clean_start = start.lower().strip()
    if clean_start == "today":
        start_date = date.today().isoformat()
    elif clean_start == "tomorrow":
        start_date = (date.today() + timedelta(days=1)).isoformat()
    else:
        start_date = start

    if end:
        clean_end = end.lower().strip()
        if clean_end == "today":
            end_date = date.today().isoformat()
        elif clean_end == "tomorrow":
            end_date = (date.today() + timedelta(days=1)).isoformat()
        else:
            end_date = end
    else:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = (start_dt + timedelta(days=max(0, days - 1))).isoformat()

    appearances = store.get_counsel_schedule(name, start_date=start_date, end_date=end_date)
    return {
        "counsel_query": name,
        "start_date": start_date,
        "end_date": end_date,
        "total_appearances": len(appearances),
        "appearances": appearances
    }


@router.get("/counsel/{name}/clashes", summary="Detect courtroom scheduling clashes for a counsel")
def get_counsel_clashes(
    name: str,
    date_str: str = Query("today", alias="date", description="Hearing date ('today', 'tomorrow', or YYYY-MM-DD)"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    clean_date = date_str.lower().strip()
    if clean_date == "today":
        target_date = date.today().isoformat()
    elif clean_date == "tomorrow":
        target_date = (date.today() + timedelta(days=1)).isoformat()
    else:
        target_date = date_str

    clashes = store.find_counsel_clashes(target_date, name)
    return {
        "counsel": name,
        "date": target_date,
        "has_clash": len(clashes) > 1,
        "clashes_count": len(clashes),
        "clash_items": clashes
    }


@router.get("/counsel/{name}/portfolio", summary="Get lifetime representation portfolio for a counsel")
def get_counsel_portfolio(
    name: str,
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    return store.get_counsel_portfolio(name)


@router.get("/judge/{name}/caseload", summary="Get judge bench caseload, hearings presided, and cases heard")
def get_judge_caseload(
    name: str,
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    return store.get_judge_caseload(name)


@router.get("/case/{case_id:path}/timeline", summary="Get chronological hearing timeline for a case")
def get_case_timeline(
    case_id: str,
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    history = store.get_case_listing_history(case_id)
    return {
        "case_query": case_id,
        "total_hearings": len(history),
        "timeline": history
    }


@router.get("/case/{case_id:path}/precedents", summary="Get multi-hop precedent citations and statutory sections for a case")
def get_case_precedents(
    case_id: str,
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    precedents = store.find_connected_precedents(case_id)
    return {
        "case_query": case_id,
        "total_precedents": len(precedents),
        "precedents": precedents
    }


@router.post("/query", response_model=CypherQueryResponse, summary="Execute raw openCypher query")
def execute_query(
    body: CypherQueryRequest,
    store: LegalGraphStore = Depends(get_graph_store)
) -> CypherQueryResponse:
    try:
        res = store.execute_raw_cypher(body.query, body.params)
        return CypherQueryResponse(
            query=res["query"],
            row_count=res["row_count"],
            rows=res["rows"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export", summary="Export graph topology in JSON, DOT, or GEXF format")
def export_graph(
    format_type: str = Query("json", alias="format", description="Export format ('json', 'dot', 'gexf')"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Any:
    try:
        output = store.export_graph_format(format_type)
        if format_type.lower() == "json":
            import json
            return json.loads(output)
        return {"format": format_type, "data": output}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/communities", summary="Detect and retrieve macro-thematic graph communities")
def get_communities(
    min_size: int = Query(2, description="Minimum nodes per community cluster"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Any:
    from lawnidhi.graph.clustering import GraphClusterEngine
    engine = GraphClusterEngine(store)
    return engine.detect_communities(min_size=min_size).model_dump()
