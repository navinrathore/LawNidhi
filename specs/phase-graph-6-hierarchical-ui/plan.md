# Phase 6 Plan: Hierarchical Graph Summarization & Interactive Web UI

## Implementation Steps

### Step 1: Community Detection Module (`lawnidhi/graph/clustering.py`)
- Define Pydantic models: `CommunityProfile`, `ClusteringSummary`.
- Implement `GraphClusterEngine`:
  - `detect_communities(min_size: int = 3) -> ClusteringSummary`
  - Compute degree centralities and top hub nodes per cluster.
  - Profile statutory, precedent, and counsel affiliations per cluster.

### Step 2: REST API Routes (`lawnidhi/server/routes/graph.py`)
- Add `GET /api/graph/communities` endpoint returning detected clusters.

### Step 3: Web UI Application (`lawnidhi/server/static/`)
- `index.html`: Modern HTML5 structure with navigation, tabs (Visual Graph Explorer, Daily Court Board, GraphRAG Search, Community Clusters, Analytics Stats), and inspector drawer.
- `index.css`: Glassmorphic dark design system with custom CSS variables, responsive grid, animations, and badge styles.
- `app.js`: Lightweight Vanilla JS frontend interacting with `/api/graph/*` and `/api/rag/*`, mounting Cytoscape.js canvas with search/filter/pan/zoom capabilities.

### Step 4: FastAPI Static Mount & SPA Routing (`lawnidhi/server/app.py`)
- Mount `/static` directory via `fastapi.staticfiles.StaticFiles`.
- Add route `GET /ui` and redirect `GET /` to UI.

### Step 5: CLI Subcommand (`cli.py graph-communities`)
- Register `graph-communities` command with table output for top clusters.

### Step 6: Test Suite (`tests/test_clustering_and_ui.py`)
- Unit tests for community detection, profile calculation, and UI endpoint availability.
