# LawNidhi Roadmap

## Completed Phases
- [x] **Phase 1.1: Legal Ontology & Embedded Graph Engine (Kùzu)** — (Completed)
- [x] **Phase 1.2: Cause List Temporal Knowledge Graph & Listing Intelligence** — (Completed)
- [x] **Phase 1.3: Clean Multi-Counsel & Multi-Edge Deduplication** — (Completed)
- [x] **Phase 3: Knowledge Graph Analytical CLI Suite** — (Completed)
- [x] **Phase 2: PDF Order Triplet Extraction & Precedent Citation Graph** — (Completed)
- [x] **Phase 4: FastAPI Graph Bridge & REST Service Layer** — (Completed)
- [x] **Phase 5: Hybrid GraphRAG Retriever (Vector + Kùzu Graph Expansion)** — (Completed)
- [x] **Phase 6: Hierarchical Graph Summarization & Interactive Web UI** — (Completed)
- [x] **Phase 7: Agentic Legal Co-Counsel (Autonomous ReAct Researcher)** — (Completed)

## Future Roadmap (Enterprise & Domain-Driven Evolution)
- [ ] **Phase 8: Domain-Driven Refactoring (DDD Bounded Contexts & Clean Architecture)**
  - Isolate domain layers: Litigation Docket, Judicial Knowledge Graph, Ingestion Engine, and Co-Counsel.
  - Formalize Aggregates (`CaseAggregate`), Immutable Value Objects (`CaseNumber`, `Citation`, `StatuteSection`), and Domain Events (`CaseListedEvent`, `OrderIngestedEvent`).
  - Introduce Hexagonal Architecture (Ports & Adapters) separating domain models from infrastructure (SQLite, Kùzu, FastAPI).
- [ ] **Phase 9: Distributed Ingestion Pipeline & Scheduled Daemon**
  - Background task queue (Celery/Temporal + Redis) for scheduled morning cause list scraping and automated retries.
  - OCR & Document-AI ingestion pipeline (MinerU/PaddleOCR/Textract) for scanned, stamped, or watermarked physical court orders.
- [ ] **Phase 10: Multi-Court & Zonal Bench Expansion**
  - Zonal NGT adapters (Western/Pune, Southern/Chennai, Eastern/Kolkata, Central/Bhopal).
  - Supreme Court of India (SCI) and High Court eCourts scrapers and ingestors with unified docket normalization.
- [ ] **Phase 11: Enterprise Persistence & Vector DB Decoupling**
  - Migrate relational state from local SQLite to PostgreSQL with connection pooling, migrations (Alembic), and row-level security.
  - Replace in-memory TF-IDF with dedicated Vector DB (Qdrant / pgvector) powered by legal-domain embeddings (`bge-large-en`) and Cross-Encoder rerankers.
  - Externalize graph engine connection pooling for multi-user concurrent traversals.
- [ ] **Phase 12: Advanced Citation Intelligence & "Shepardizing" Engine**
  - Graph-based precedent validity checking: automatically trace whether cited precedents are upheld, distinguished, or overruled.
  - Global GraphRAG community summaries for macro-level judicial trend analysis across tribunals and years.
  - Automated RAG evaluation benchmark harness (Ragas / TruLens / LLM Judge).
- [ ] **Phase 13: Enterprise Multi-Tenancy, RBAC & Governance**
  - Law-firm multi-tenant isolation and workspace partitioning.
  - Role-Based Access Control (Managing Partner, Senior Counsel, Associate, Paralegal, Client Read-Only).
  - Enterprise SSO (SAML 2.0, OAuth2/OIDC) and tamper-evident legal audit trails for data provenance.
- [ ] **Phase 14: Proactive Litigator Alerting & CMS Integration**
  - Real-time morning hearing alerts and order notifications via WhatsApp, Slack, and Email webhooks.
  - Two-way calendar synchronization (Google Calendar / iCal) and litigation practice management exports.

