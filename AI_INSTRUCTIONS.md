# AI Instructions for LawNidhi

This document outlines the architectural rules and Spec-Driven Development (SDD) methodology for the LawNidhi project.

## Spec-Driven Development (SDD) Rules

LawNidhi strictly follows the SDD lifecycle. **Never write implementation code without an approved spec.**

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

- **CLI First**: LawNidhi is a CLI tool. Use `argparse` with command groups.
- **SQLite Database**: All case data is stored locally in SQLite (`lawnidhi.db`). Use the existing repo pattern in `lawnidhi.db` for access.
- **Agentic Queries (Future)**: When introducing LLM features, strictly adhere to the `BaseLLMClient` unified provider pattern (detailed in `docs/agentic_architecture.md`). Never execute raw subprocesses dynamically without explicit sandboxing.

## Code Quality Gates
- Follow PEP-8.
- Use type hints for all function signatures.
- Log appropriately.
