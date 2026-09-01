# Phase 4 Plan: FastAPI Graph Bridge & REST Service Layer

## Implementation Steps

### Step 1: Server Package Initialization (`lawnidhi/server/`)
- Create `lawnidhi/server/__init__.py`.
- Create `lawnidhi/server/app.py`:
  - FastAPI app initialization with lifespan context manager for `LegalGraphStore`.
  - CORS middleware allowing all origins (`*`) for local UI visualizer development.
  - Health check endpoint `GET /health`.

### Step 2: Graph Routes Module (`lawnidhi/server/routes/graph.py`)
- Implement route handlers for:
  - `GET /api/graph/stats`
  - `GET /api/graph/daily-board`
  - `GET /api/graph/counsel/{name}/cases`
  - `GET /api/graph/counsel/{name}/clashes`
  - `GET /api/graph/counsel/{name}/portfolio`
  - `GET /api/graph/judge/{name}/caseload`
  - `GET /api/graph/case/{case_id}/timeline`
  - `GET /api/graph/case/{case_id}/precedents`
  - `POST /api/graph/query` (with Pydantic `CypherQueryRequest` body)
  - `GET /api/graph/export`

### Step 3: Orders Routes Module (`lawnidhi/server/routes/orders.py`)
- Implement route handlers for:
  - `POST /api/orders/extract` (accepting file upload or file path)
  - `POST /api/orders/sync`

### Step 4: CLI Subcommand Integration (`cli.py serve`)
- Register `serve` subparser with `--host`, `--port`, and `--reload` options.
- Integrate `uvicorn.run()` runner in `cli.py`.

### Step 5: Unit & API Test Suite (`tests/test_server_api.py`)
- Implement comprehensive test suite using `fastapi.testclient.TestClient`.
- Verify all endpoints with both valid and invalid/empty inputs.
