# LawNidhi Backlog

This document tracks deferred items, technical debt, and future ideas that are not part of the active phase.

## Technical Debt
- [ ] Migrate to a formal testing suite using `pytest`.
- [ ] Ensure all code uses strict type-hinting across domain and graph stores.
- [ ] Decouple database path resolution from `__file__` in LawNidhi. Use environment variables (e.g., `LAWNIDHI_DB_PATH`) so that dependent applications (like Open-NotebookLM) can inject the correct database path dynamically without relying on editable pip installs, which break when the project directory is moved.
- [ ] Abstract direct SQLite and Kùzu queries behind domain repository interfaces (Hexagonal Architecture).

## Domain-Driven Design (DDD) Refinement
- [ ] **Ubiquitous Language & Bounded Contexts**: Formally document ubiquitous language across Litigation Docket, Knowledge Graph, Ingestion, and Co-Counsel domains.
- [ ] **Aggregate Invariants**: Implement `CaseAggregate` enforcing invariants around hearing sequencing, order attachments, and status progression (`REGISTERED` -> `LISTED` -> `HEARING_HELD` -> `DISPOSED`).
- [ ] **Value Objects**: Introduce immutable value objects for `CaseNumber`, `Citation`, `StatuteSection`, and `CourtVenue` with built-in validation rules.
- [ ] **Domain Events**: Implement an in-memory or message-bus Domain Event dispatcher (`CaseListedEvent`, `OrderIngestedEvent`, `PrecedentOverruledEvent`) to decouple ingestion, graph indexing, and notifications.
- [ ] **Repository Ports**: Define abstract repository interfaces (`ICaseRepository`, `ILegalGraphRepository`, `IVectorIndexRepository`) isolating domain models from storage implementations.
- [ ] **Lightweight TDD Test Fixtures**: Establish reusable test fixtures (static order PDF snippets, in-memory Kùzu graphs, and sample case numbers) to accelerate test-first design for DDD aggregates and parsers.


## Enterprise Architecture & Infrastructure
- [ ] Sandbox the agent execution using a Docker container if we allow dynamic python code execution.
- [x] Build an embedded Legal Knowledge Graph (`kuzu`/`networkx`) linked with `lawnidhi.db` to extract entities (Judges, Counsels, Statutes, Precedents) from PDF orders for graph-assisted legal search.
- [ ] **PostgreSQL Migration**: Replace SQLite with PostgreSQL, incorporating connection pooling (SQLAlchemy / asyncpg) and Alembic migrations.
- [ ] **Production Vector DB**: Implement Qdrant/pgvector adapter with dense legal embeddings (`bge-large-en`) and Cross-Encoder reranking.
- [ ] **Distributed Ingestion Queue**: Deploy Celery or Temporal task workers with Redis broker for asynchronous cause-list scraping and PDF downloading.
- [ ] **OCR Ingestion Engine**: Integrate MinerU / PaddleOCR / AWS Textract for parsing poor-quality scanned Indian court orders.
- [ ] **Multi-Tenancy & RBAC**: Tenant partitioning per law firm with role-based permissions (Partner, Counsel, Associate, Paralegal).
- [ ] **Enterprise SSO & Audit Trail**: SAML 2.0 / OAuth2 authentication with immutable audit logging for legal compliance.

## Advanced Legal AI & RAG
- [ ] **Shepardizing & Citation Network**: Automated graph traversal to determine if cited authorities remain good law or have been overruled/modified.
- [ ] **Global GraphRAG Community Summaries**: Hierarchical summaries over precedent clusters for high-level judicial trend insights.
- [ ] **RAG Evaluation Harness**: Automated benchmarking suite using Ragas / TruLens to measure legal faithfulness and citation recall.
- [ ] **Cause List Webhook Alerts**: Real-time push notifications (WhatsApp / Slack / Email) for listing dates and freshly uploaded judicial orders.

