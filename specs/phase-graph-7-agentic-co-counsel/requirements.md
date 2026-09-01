# Phase 7 Requirements: Agentic Legal Co-Counsel (Autonomous ReAct Legal Researcher)

## Objective
Build a self-contained, autonomous Agentic Legal Co-Counsel inside LawNidhi that combines multi-step ReAct (Reasoning + Action) planning, tool execution over the Kùzu Knowledge Graph, Hybrid GraphRAG passage retrieval, and structured legal drafting.

## Background & Problem
While individual CLI commands and REST endpoints exist for specific queries, complex litigation research requires multi-step autonomous reasoning:
- *"Check if Senior Counsel Bhanwar Pal Singh has any court clashes tomorrow in Court 1 and Court 2, summarize the matters he is appearing in, and retrieve the applicable statutory sections and precedent rulings."*
- *"Prepare a complete case brief for OA 985/2019 including invoked Water Act sections, Supreme Court binding ratios, and previous listing intervals."*

An agentic ReAct loop allows an AI assistant to iteratively decide which tools to invoke, analyze observations, and synthesize comprehensive legal briefs.

## Workspace Design Constraints (Mandatory Rules)
- **Rule 1 (ReAct Loop Safety)**: Enforce a hard `max_loops = 12` bound to guarantee loop termination and prevent runaway execution.
- **Rule 2 (Provider Agnosticism)**: Provider-agnostic LLM interface with fallback to local rule-based deterministic planning if no external API key is configured.
- **Rule 7 (Structured Outputs)**: Pydantic schemas for `AgentAction`, `AgentObservation`, `CoCounselResponse`, and `CaseBrief`.
- **Rule 11 (Hybrid Supervisory Wrapper)**: All tool execution logic is 100% deterministic; the AI layer acts strictly as a supervisory orchestrator.

## Functional Requirements

### 1. ReAct Agent Engine (`lawnidhi/agent/co_counsel.py`)
- Tool Registry:
  - `query_graph(cypher)`: Execute openCypher queries on Kùzu DB.
  - `get_precedents(case)`: Find multi-hop precedent citations and statutory sections.
  - `retrieve_hybrid_rag(query, top_k)`: Retrieve semantic passage excerpts + connected graph subgraphs.
  - `check_counsel(counsel, date)`: Check court listings and detect courtroom conflicts.
  - `get_judge_caseload(judge)`: Check bench caseload and hearing stats.
  - `generate_case_brief(case)`: Assemble a structured case brief.
- Multi-step ReAct loop:
  - Step 1: Analyze user intent $\rightarrow$ produce `Thought` and `Action(tool_name, tool_input)`.
  - Step 2: Execute tool deterministically $\rightarrow$ produce `Observation`.
  - Step 3: Iterate until `Final Answer` is reached or `max_loops` is hit.

### 2. REST API Endpoint (`lawnidhi/server/routes/agent.py`)
- `POST /api/agent/chat`: Accepts `{"query": str, "max_loops": int}`, returns structured `CoCounselResponse` with full reasoning trace and final answer.

### 3. Web UI Integration (`lawnidhi/server/static/`)
- Interactive Co-Counsel Chat Drawer with real-time thought step visualization, tool call badges, and Markdown rendering.

### 4. CLI Subcommand (`cli.py ask`)
- `python projects/LawNidhi/cli.py ask "<query>" [--max-loops 10] [--verbose]`
