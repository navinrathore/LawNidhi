# AI Instructions for NyayaGraph (featuring VidhiGraph)

This document outlines the architectural rules and Spec-Driven Development (SDD) methodology for the **NyayaGraph** project.

## Spec-Driven Development (SDD) Rules

NyayaGraph strictly follows the SDD lifecycle. **Never write implementation code without an approved spec.**

### The SDD Phase Lifecycle
Features are developed in named phases (e.g., `specs/phase-setup/`). Each phase directory MUST contain:
1. `requirements.md`: What is being built and why.
2. `plan.md`: The technical design and steps.
3. `validation.md`: How the changes will be tested.

### Phase Completion Checklist
Before moving to the next phase, the AI must ensure:
- [ ] Spec files are complete and committed.
- [ ] Code is fully implemented according to the plan.
- [ ] The full test suite passes.
- [ ] Linters/formatters (`ruff`) pass without errors.
- [ ] `specs/roadmap.md` is updated to mark the phase as `(Completed)`.
- [ ] Deferred items or technical debt are logged in `specs/backlog.md`.
- [ ] All changes are committed to Git.

## Project Architecture & Patterns

- **CLI First**: NyayaGraph is operated via CLI. Use `argparse` with command groups (`nyayagraph`).
- **SQLite Database**: All relational docket data is stored locally in SQLite (`nyayagraph.db`). Use the repo pattern in `nyayagraph.db` for access.
- **Knowledge Graph**: Embedded Property Graph is backed by Kùzu (`data/nyayagraph_graph/kuzu_db`).
- **VidhiGraph Subsystem**: Dedicated statutory engine for Acts, Sections, Rules, and Gazette Notifications.
- **Agentic Queries**: Adhere to the `BaseLLMClient` unified provider pattern (detailed in `docs/agentic_architecture.md`). Never execute raw subprocesses dynamically without explicit sandboxing. Hard bound loops (`max_loops <= 12`).

## Code Quality Gates
- Follow PEP-8.
- Use type hints for all function signatures.
- Log appropriately.

## Pragmatic (Lightweight) TDD Strategy
NyayaGraph embraces a **selective, high-ROI TDD approach** rather than dogmatic test-everything-first:

- **Apply TDD (Test-First)** to:
  - **Domain Models & Invariants (DDD)**: Value objects (`CaseNumber`, `Citation`, `StatuteSection`), state transition rules, and aggregate invariants. These are pure Python with zero I/O and execute in milliseconds.
  - **Text Parsers & Extraction Regex**: PDF order triplet extractors, cause list regex patterns, and counsel string parsers. Use static sample fixtures to write failing tests for new edge cases before tweaking parsing heuristics.
  - **Deterministic GraphRAG & Cypher Queries**: Test multi-hop expansions (`GraphContextExpander`) and assembly logic against an in-memory/fixture graph store.

- **SKIP TDD** for:
  - **Live External Scraping & CAPTCHA**: Do not unit test against live court network endpoints. Use recorded HTML/PDF fixtures for unit tests, and relegate live network checks to manual or scheduled smoke tests.
  - **Generative LLM Text Synthesis**: Do not write rigid string-matching assertions on model text. Test strict Pydantic output schemas instead, and evaluate generation quality using benchmarks/LLM-as-a-judge.
  - **UI Styling & HTML Layouts**: Verify visually in the browser rather than writing fragile layout tests.
