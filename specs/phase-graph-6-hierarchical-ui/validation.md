# Phase 6 Validation Plan: Hierarchical Graph Summarization & Web UI

## Automated Test Coverage (`tests/test_clustering_and_ui.py`)

1. **Community Detection Engine**:
   - Verify graph partitioning on test graph produces valid clusters with non-overlapping node sets.
   - Verify calculation of top hubs, statutes, and dominant entity types.
2. **REST API Endpoint (`GET /api/graph/communities`)**:
   - Verify 200 OK response with `total_communities > 0` and structured `communities` list.
3. **Web UI Static Endpoint (`GET /ui` and `GET /static/index.html`)**:
   - Verify 200 OK response with HTML content type.
4. **CLI Subcommand (`graph-communities`)**:
   - Verify `python projects/LawNidhi/cli.py graph-communities` executes without error and prints formatted community tables.
