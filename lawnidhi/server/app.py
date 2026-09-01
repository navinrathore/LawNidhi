"""app.py: Main FastAPI application factory for LawNidhi REST Service."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.server.routes.graph import router as graph_router
from lawnidhi.server.routes.orders import router as orders_router
from lawnidhi.server.routes.rag import router as rag_router


def get_default_db_path() -> str:
    """Resolve default Knowledge Graph database directory."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(root_dir, "data", "lawnidhi_graph", "kuzu_db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for initializing and cleaning up shared resources."""
    db_path = getattr(app.state, "custom_db_path", None) or get_default_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize singleton LegalGraphStore
    store = LegalGraphStore(db_path=db_path)
    app.state.graph_store = store
    try:
        yield
    finally:
        store.close()


def create_app(db_path: str = None) -> FastAPI:
    """Factory to create a configured FastAPI application instance."""
    app = FastAPI(
        title="LawNidhi Knowledge Graph API",
        description="REST Service Layer for NGT Legal Knowledge Graph, Precedent Discovery, and Judicial Order Triplet Extraction.",
        version="1.0.0",
        lifespan=lifespan
    )

    if db_path:
        app.state.custom_db_path = db_path

    # CORS Middleware (Enable web dashboard / Cytoscape visualizer access)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(graph_router)
    app.include_router(orders_router)
    app.include_router(rag_router)

    @app.get("/", summary="API Root", tags=["System"])
    def root() -> Dict[str, str]:
        return {
            "name": "LawNidhi Knowledge Graph API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "status": "online"
        }

    @app.get("/health", summary="Health Check", tags=["System"])
    def health() -> Dict[str, str]:
        return {"status": "healthy"}

    return app


# Default app instance for ASGI servers (e.g. uvicorn lawnidhi.server.app:app)
app = create_app()
