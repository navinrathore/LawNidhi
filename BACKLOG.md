# 🏛️ LawNidhi AI Master Backlog

This is the persistent record of all features, optimizations, and roadmap items for the LawNidhi AI Legal Workspace.

## 🟢 [COMPLETED & READY]
- [x] **DONE** `[CORE]` **Unified RAG Parity** `***`: Parity between General and Litigation notebooks for document indexing.
- [x] **DONE** `[CORE]` **Deep Delete Engine** `***`: Sequences: Index Purge -> Physical File Removal -> Manifest Sync.
- [x] **DONE** `[PERF]` **Dev Utility - Re-indexing** `**`: Allows rebuilding vector stores with new parameters.
- [x] **DONE** `[PERF]` **Performance - Dynamic Top-K** `*`: Retrieval depth is now configurable via `RAG_TOP_K` in `.env`.
- [x] **DONE** `[PERF]` **Performance - Similarity Threshold** `*`: Retrieval noise filtering via `RAG_SIMILARITY_THRESHOLD`.
- [x] **DONE** `[CORE]` **Context Windowing** `**`: Auto-retrieve adjacent chunks (N+/-1) to provide context for single-line hits.

## 🟡 [CORE] RAG Roadmap (Pending Implementation)
- [x] **DONE** `[CORE]` **1. Reranking (Cross-Encoders)** `***`: Implement secondary re-scoring for Top-K to drastically improve accuracy.
- [/] **ACTIVE** `[CORE]` **3. Hybrid Search** `***`: Integrate BM25 (Keyword) search alongside Vector search for legal code and citation accuracy.
- [ ] **PENDING** `[CORE]` **4. Physical Index Verification** `**`: Implement backend checks to ensure `.index` files exist before reporting status.
- [ ] **PENDING** `[CORE]` **5. System Localization** `*`: Refactor internal tool descriptions and logs to prioritize English while supporting localized legal terminology.
- [ ] **PENDING** `[CORE]` **6. Universal Hierarchy Mapper** `***`: SCI > NGT > High Courts > Tribunals.
- [ ] **PENDING** `[CORE]` **7. Filename Prioritization** `**`: Ensure Supreme Court/NGT scraper prepends `SCI_` or `NGT_` for automatic prioritization.
- [ ] **PENDING** `[PERF]` **8. Lazy Loading Optimization** `**`: Refactor heavy imports in RAG core to improve startup speed.

## 🔵 [UI/UX] Interface & Experience
- [ ] **PENDING** `[UI/UX]` **Storage Sync** `**`: Persist `selectedFiles` state across browser sessions.
- [ ] **PENDING** `[UI/UX]` **Progress Indicators** `**`: Add visual indicators for "Computing Embeddings" per-file in the sidebar.
- [ ] **PENDING** `[UI/UX]` **Delete Permissions** `*`: Configuration toggle to disable "Delete" for specific source types.
- [ ] **PENDING** `[UI/UX]` **Mobile Responsiveness** `**`: Verify sidebars and modals follow glassmorphism standards on small screens.
- [x] **DONE** `[UI/UX]` **Suggested Questions** `***`: Automatically generate 3-5 short "ice-breaker" questions based on notebook sources (NotebookLM Parity).

## 🔴 [ROADMAP] Future Scaling
- [ ] **PENDING** `[CORE]` **Multi-Vector Retrieval** `***`: Support for Tables and Images extraction from legal documents via MinerU.
- [ ] **PENDING** `[CORE]` **External Vector DB** `***`: Abstraction layer to support ChromaDB, Qdrant, or pgvector for enterprise-scale litigation.
- [x] **DONE** `[CORE]` **Legal Knowledge Graph & Citation Network** `***`: Ingest parsed NGT orders and cause lists into an embedded graph DB (Kùzu/NetworkX). Model `(Case)-[:CITES_PRECEDENT]->(Case)`, `(Counsel)-[:REPRESENTS]->(Party)`, and `(Case)-[:INVOKES_STATUTE]->(Section)` for multi-hop legal analytics and precedent discovery.

## 🏛️ [ENTERPRISE & DDD] Domain-Driven Design Architecture
- [ ] **PENDING** `[DDD]` **Ubiquitous Language & Bounded Contexts** `***`: Formally delineate domain boundaries: Litigation Docket, Judicial Knowledge Graph, Ingestion Engine, Co-Counsel Agent, and Identity/Tenancy.
- [ ] **PENDING** `[DDD]` **Aggregate Roots & Domain Invariants** `***`: Model `CaseAggregate` to enforce business invariants regarding hearing chronologies, status lifecycle (`REGISTERED` -> `LISTED` -> `HEARING_HELD` -> `DISPOSED`), and attached judicial orders.
- [ ] **PENDING** `[DDD]` **Immutable Value Objects** `**`: Standardize `CaseNumber` (e.g., `83/2025`), `ReporterCitation` (e.g., `(1996) 5 SCC 647`), `StatuteSection`, and `CourtVenue` with strict validation rules.
- [ ] **PENDING** `[DDD]` **Event-Driven Architecture (Domain Events)** `***`: Decouple components using an in-memory/message-bus event dispatcher (`CaseListedEvent`, `OrderIngestedEvent`, `PrecedentOverruledEvent`) to trigger indexing and notifications asynchronously.
- [ ] **PENDING** `[DDD]` **Hexagonal Architecture (Ports & Adapters)** `***`: Abstract persistence behind domain repository ports (`ICaseRepository`, `ILegalGraphRepository`, `IVectorStoreRepository`), eliminating direct SQLite/Kùzu dependencies from core domain logic.
- [ ] **PENDING** `[DDD]` **Lightweight TDD Test Fixtures** `**`: Establish fast, zero-I/O test fixtures (static order PDF snippets, in-memory Kùzu graphs) for test-first development of domain models and extraction regex while skipping live scrapers and LLM text generation.


## ⚡ [DISTRIBUTED PIPELINES] Multi-Court Ingestion & OCR
- [ ] **PENDING** `[INGEST]` **Asynchronous Task Queue** `***`: Deploy Celery or Temporal with Redis broker for resilient, scheduled morning scraping with retry policies and CAPTCHA solving.
- [ ] **PENDING** `[INGEST]` **OCR & Document-AI Engine** `***`: Integrate MinerU / PaddleOCR / AWS Textract for high-accuracy parsing of watermarked, scanned, or degraded Indian court orders.
- [ ] **PENDING** `[INGEST]` **National Court Adapters** `***`: Expand scraping coverage to all NGT Zonal Benches (Pune, Chennai, Kolkata, Bhopal), High Courts, and Supreme Court of India (SCI) eCourts portals.

## 🗄️ [STORAGE & INFRASTRUCTURE] Enterprise Persistence
- [ ] **PENDING** `[DB]` **PostgreSQL Migration** `***`: Transition core transactional data from local SQLite (`lawnidhi.db`) to PostgreSQL with connection pooling, Alembic migrations, and Row-Level Security (RLS).
- [ ] **PENDING** `[VECTOR]` **Production Vector Store** `***`: Replace in-memory TF-IDF with Qdrant or pgvector using domain-tailored embeddings (`bge-large-en`) and Cross-Encoder rerankers.
- [ ] **PENDING** `[GRAPH]` **Clustered Graph Database** `**`: Connection pooling and multi-client concurrent read/write scaling for Kùzu or dedicated graph backends (Memgraph/Neo4j).

## 🛡️ [SECURITY & MULTI-TENANCY] Enterprise Governance & Access
- [ ] **PENDING** `[AUTH]` **Multi-Tenant Partitioning** `***`: Strict tenant isolation for multiple law firms or legal departments sharing a single platform instance.
- [ ] **PENDING** `[AUTH]` **Granular RBAC** `**`: Role definitions for Managing Partner, Senior Counsel, Associate, Paralegal, and Client Read-Only.
- [ ] **PENDING** `[COMPLIANCE]` **Enterprise SSO & Audit Logging** `***`: SAML 2.0 / OAuth2 / OIDC authentication with tamper-evident, append-only audit trails for query, retrieval, and document access history.

## 🧠 [ADVANCED LEGAL AI] Shepardizing & Global GraphRAG
- [ ] **PENDING** `[RAG]` **"Shepardizing" Precedent Engine** `***`: Automated citation validity graph traversal to flag whether cited authorities are affirmed, distinguished, or overruled by subsequent decisions.
- [ ] **PENDING** `[RAG]` **Global GraphRAG Community Summaries** `***`: Hierarchical graph clustering (Louvain/Leiden) to generate high-level judicial summaries and trend analyses across tribunal benches and years.
- [ ] **PENDING** `[EVAL]` **RAG Evaluation Harness** `**`: Continuous benchmark harness using Ragas / TruLens / LLM Judge tracking legal faithfulness, statutory recall, and citation hallucination rates.

## 🔔 [INTEGRATIONS] Proactive Alerts & Calendar Sync
- [ ] **PENDING** `[ALERTS]` **Real-time Cause List Alerts** `**`: Webhook dispatchers sending morning hearing alerts and order notifications via WhatsApp, Slack, and Email.
- [ ] **PENDING** `[SYNC]` **Litigation Calendar Sync** `**`: Two-way synchronization with Google Calendar, iCal, and practice management tools (CMS).

## 🟣 [PROMPTS] Prompt Review & Refinement
- [ ] **PENDING** `[PROMPT]` **Review Litigation Gaps** `***`: Audit `prompts_repo.py` to identify missing specialized legal/case prompts.
- [x] **DONE** `[PROMPT]` **Add Litigation System Prompt** `**`: Create a specialized "Legal Specialist" role for LawNidhi Case Notebooks.
- [ ] **PENDING** `[PROMPT]` **Add Irish/Indian Formatters** `**`: Ensure prompt templates support regional court order structures (Dates, Citations).
- [x] **DONE** `[PROMPT]` **Refine Extraction Logic** `**`: Improve Petitioner/Respondent/Held extraction success rates with better few-shot examples.

## 🟢 [NOTES] Custom Observations & Tweaks
- `*` **Generic Policy**: Create a prompt so that generic policy can be forced.
- `*` **Backlog Tracking**: Maintain this file to trace TODO/Suggested items.
- `**` **Prompt Repo Audit**: Prompt Repo file needs update and finetuning.