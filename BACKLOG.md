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
- [ ] **PENDING** `[CORE]` **External Vector DB** `***`: Abstraction layer to support ChromaDB or Qdrant for enterprise-scale litigation.
- [ ] **PENDING** `[CORE]` **Legal Knowledge Graph & Citation Network** `***`: Ingest parsed NGT orders and cause lists into an embedded graph DB (Kùzu/NetworkX). Model `(Case)-[:CITES_PRECEDENT]->(Case)`, `(Counsel)-[:REPRESENTS]->(Party)`, and `(Case)-[:INVOKES_STATUTE]->(Section)` for multi-hop legal analytics and precedent discovery.

## 🟣 [PROMPTS] Prompt Review & Refinement
- [ ] **PENDING** `[PROMPT]` **Review Litigation Gaps** `***`: Audit `prompts_repo.py` to identify missing specialized legal/case prompts.
- [x] **DONE** `[PROMPT]` **Add Litigation System Prompt** `**`: Create a specialized "Legal Specialist" role for LawNidhi Case Notebooks.
- [ ] **PENDING** `[PROMPT]` **Add Irish/Indian Formatters** `**`: Ensure prompt templates support regional court order structures (Dates, Citations).
- [x] **DONE** `[PROMPT]` **Refine Extraction Logic** `**`: Improve Petitioner/Respondent/Held extraction success rates with better few-shot examples.

## 🟢 [NOTES] Custom Observations & Tweaks
- `*` **Generic Policy**: Create a prompt so that generic policy can be forced.
- `*` **Backlog Tracking**: Maintain this file to trace TODO/Suggested items.
- `**` **Prompt Repo Audit**: Prompt Repo file needs update and finetuning.