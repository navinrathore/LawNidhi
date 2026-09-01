# Phase 7 Plan: Agentic Legal Co-Counsel

## Implementation Steps

### Step 1: Agent Schemas & Tool Definitions (`lawnidhi/agent/schema.py`)
- Pydantic models:
  - `AgentStep`: thought, action_tool, action_input, observation.
  - `CoCounselResponse`: query, final_answer, steps, tools_invoked, loop_count, execution_time_sec.
  - `CaseBrief`: case_number, case_title, court_no, date, presiding_coram, applicants, respondents, counsels, invoked_statutes, cited_precedents, order_summary.

### Step 2: Deterministic Legal Tool Registry (`lawnidhi/agent/tools.py`)
- Implement `LegalToolRegistry`:
  - `query_graph(cypher: str)`
  - `get_precedents(case_id_or_number: str)`
  - `retrieve_hybrid_rag(query: str, top_k: int)`
  - `check_counsel(counsel_name: str, date: str)`
  - `get_judge_caseload(judge_name: str)`
  - `generate_case_brief(case_id_or_number: str)`

### Step 3: ReAct Loop Engine (`lawnidhi/agent/co_counsel.py`)
- Implement `AgenticCoCounsel`:
  - Intent router & ReAct loop with `max_loops = 12`.
  - Deterministic planner fallback (pattern matching & multi-tool pipeline) when running offline or without API key.
  - Structured step execution and final synthesis generation.

### Step 4: REST API Route (`lawnidhi/server/routes/agent.py`)
- Add `agent_router` with `POST /api/agent/chat` and `POST /api/agent/brief`.
- Register in `lawnidhi/server/app.py`.

### Step 5: Web UI Assistant Integration (`lawnidhi/server/static/`)
- Add Co-Counsel Chat Drawer tab & floating AI action button in `index.html`.
- Add chat drawer styling in `index.css`.
- Add conversational client logic in `app.js`.

### Step 6: CLI Subcommand (`cli.py ask`)
- Register `ask` command in `cli.py`.

### Step 7: Test Suite (`tests/test_agentic_co_counsel.py`)
- Unit and integration tests for tools, ReAct loop bounds, brief generation, and API endpoints.
