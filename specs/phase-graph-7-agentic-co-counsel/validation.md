# Phase 7 Validation Plan: Agentic Legal Co-Counsel

## Automated Test Coverage (`tests/test_agentic_co_counsel.py`)

1. **Tool Registry Verification**:
   - `query_graph` runs valid Cypher and returns rows.
   - `get_precedents` resolves case and returns precedent links.
   - `retrieve_hybrid_rag` returns passages and statutory sections.
   - `check_counsel` detects appearances and clashes.
   - `generate_case_brief` produces a complete Pydantic `CaseBrief`.
2. **ReAct Loop Hard Limits (Rule 1)**:
   - Verify agent terminates within `max_loops` without infinite looping.
3. **Complex Multi-Step Queries**:
   - Query: *"Check cases for Bhanwar Pal Singh and summarize his precedents."*
   - Query: *"Prepare a complete case brief for OA 985/2019."*
4. **REST API Endpoint (`POST /api/agent/chat`)**:
   - Returns 200 OK with `final_answer` and `steps`.
5. **CLI Subcommand (`ask`)**:
   - `python projects/LawNidhi/cli.py ask "Summarize case 985/2019" --verbose` runs without error.
