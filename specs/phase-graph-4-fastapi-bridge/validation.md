# Phase 4 Validation Plan: FastAPI Graph Bridge & REST Service Layer

## Automated API Tests (`tests/test_server_api.py`)

Using `fastapi.testclient.TestClient`:
1. `GET /health` $\rightarrow$ 200 OK `{"status": "healthy"}`.
2. `GET /api/graph/stats` $\rightarrow$ 200 OK with `total_nodes > 0` and `entity_breakdown`.
3. `GET /api/graph/daily-board?date=2026-09-01` $\rightarrow$ 200 OK with array of case items.
4. `GET /api/graph/counsel/Bhanwar%20Pal%20Singh/portfolio` $\rightarrow$ 200 OK with `total_cases >= 20`.
5. `GET /api/graph/judge/Prakash%20Shrivastava/caseload` $\rightarrow$ 200 OK with `total_hearings > 0`.
6. `GET /api/graph/case/985/2019/precedents` $\rightarrow$ 200 OK with `precedents` array.
7. `POST /api/graph/query` with `{"query": "MATCH (n:LegalEntity) RETURN count(n)"}` $\rightarrow$ 200 OK with row count.
8. `GET /api/graph/export?format=json` $\rightarrow$ 200 OK with valid JSON topology.

## Manual HTTP Verification via cURL

```bash
# 1. Start server in background
python projects/LawNidhi/cli.py serve --port 8000

# 2. Check health and stats
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/api/graph/stats | jq .

# 3. Check counsel portfolio
curl -s "http://127.0.0.1:8000/api/graph/counsel/Bhanwar%20Pal%20Singh/portfolio" | jq .

# 4. Check precedent citations
curl -s "http://127.0.0.1:8000/api/graph/case/985%2F2019/precedents" | jq .

# 5. Run raw Cypher query
curl -s -X POST http://127.0.0.1:8000/api/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (j:LegalEntity {entity_type: \"JUDGE\"}) RETURN j.name LIMIT 5"}' | jq .
```
