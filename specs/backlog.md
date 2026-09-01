# LawNidhi Backlog

This document tracks deferred items, technical debt, and future ideas that are not part of the active phase.

## Technical Debt
- [ ] Migrate to a formal testing suite using `pytest`.
- [ ] Ensure all code uses strict type-hinting.
- [ ] Decouple database path resolution from `__file__` in LawNidhi. Use environment variables (e.g., `LAWNIDHI_DB_PATH`) so that dependent applications (like Open-NotebookLM) can inject the correct database path dynamically without relying on editable pip installs, which break when the project directory is moved.

## Ideas
- [ ] Sandbox the agent execution using a Docker container if we allow dynamic python code execution.
- [ ] Build an embedded Legal Knowledge Graph (`kuzu`/`networkx`) linked with `lawnidhi.db` to extract entities (Judges, Counsels, Statutes, Precedents) from PDF orders for graph-assisted legal search.
