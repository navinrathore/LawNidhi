"""orders.py: FastAPI route handlers for Order PDF triplet extraction and synchronization."""
from __future__ import annotations
import os
import shutil
import tempfile
from typing import Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from pydantic import BaseModel, Field

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.parsers.ngt.order_parser import NGTOrderParser
from lawnidhi.graph.order_sync import ingest_order_extraction, sync_all_orders
from lawnidhi.server.routes.graph import get_graph_store

router = APIRouter(prefix="/api/orders", tags=["Order Extraction"])


class OrderExtractPathRequest(BaseModel):
    pdf_path: str = Field(description="Absolute or relative path to the local PDF file")
    ingest: bool = Field(default=False, description="Whether to automatically ingest into Knowledge Graph")


@router.post("/extract-file", summary="Extract metadata, statutes, and citations from an uploaded order PDF")
async def extract_uploaded_order(
    file: UploadFile = File(...),
    ingest: bool = Query(False, description="Whether to merge extracted triplets into Knowledge Graph"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        parser = NGTOrderParser()
        extraction = parser.parse_order(tmp_path)
        result = extraction.model_dump()

        if ingest:
            stats = ingest_order_extraction(store, extraction)
            result["ingestion_stats"] = stats

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/extract-path", summary="Extract metadata, statutes, and citations from a server-side PDF path")
def extract_path_order(
    body: OrderExtractPathRequest,
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    if not os.path.exists(body.pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found: {body.pdf_path}")

    try:
        parser = NGTOrderParser()
        extraction = parser.parse_order(body.pdf_path)
        result = extraction.model_dump()

        if body.ingest:
            stats = ingest_order_extraction(store, extraction)
            result["ingestion_stats"] = stats

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


@router.post("/sync", summary="Batch synchronize all order PDFs in a directory into the Knowledge Graph")
def sync_orders_directory(
    directory: Optional[str] = Query(None, description="Directory containing PDF files (default: projects/LawNidhi/data/orders)"),
    store: LegalGraphStore = Depends(get_graph_store)
) -> Dict[str, Any]:
    orders_dir = directory or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "orders")
    if not os.path.isdir(orders_dir):
        raise HTTPException(status_code=404, detail=f"Orders directory not found: {orders_dir}")

    summary = sync_all_orders(store, orders_dir)
    return summary
