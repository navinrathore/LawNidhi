# Phase 6 Requirements: Hierarchical Graph Summarization & Interactive Web UI

## Objective
Implement hierarchical community detection (clustering) across the LawNidhi Knowledge Graph and build a modern, high-performance, dark-mode Web UI with interactive Cytoscape.js visual graph exploration, cause list daily board viewer, community cluster dashboards, and Hybrid GraphRAG search.

## Background & Problem
1. **High Graph Density**: With 918+ nodes and 2,659+ relationships, visual and analytical comprehension requires hierarchical macro-clustering (identifying thematic clusters like *Industrial Effluent / Water Act*, *Municipal Solid Waste / Urban Bodies*, *Forest Encroachment / Mining*).
2. **User Experience**: Command-line interfaces and raw REST APIs are essential for developer pipelines, but legal practitioners, advocates, and judicial researchers require an interactive, visual web dashboard to explore citation networks, browse daily boards, and perform GraphRAG queries intuitively.

## Architecture & Principles
- **Algorithmic Graph Partitioning**: Use NetworkX modularity-based community detection (`greedy_modularity_communities` / Louvain) to segment the graph into cohesive legal thematic clusters without human labeling.
- **Modern Web Aesthetics**: Single-Page Application (SPA) with Vanilla JS/CSS, modern typography (Inter / Outfit / Playfair Display), sleek dark glassmorphism, responsive sidebar navigation, and interactive Cytoscape.js canvas.
- **Embedded Static Serving**: Served directly by the FastAPI backend at `/ui` and `/` without separate frontend build infrastructure.

## Functional Requirements

### 1. Graph Community Detection Engine (`lawnidhi/graph/clustering.py`)
- Convert Kùzu property graph to an undirected projected NetworkX graph.
- Execute modularity community detection to identify dense sub-networks.
- Generate community summaries:
  - Total nodes and density.
  - Dominant entity types (Cases, Counsels, Judges, Statutes).
  - Central hubs (highest degree nodes).
  - Thematic keywords.

### 2. Interactive Web Application (`lawnidhi/server/static/`)
- **Interactive Graph Visualizer (Cytoscape.js)**:
  - Color-coded node types (Case = Indigo, Counsel = Emerald, Judge = Amber, Statute = Cyan, Party = Gray, Hearing = Purple).
  - Dynamic physics layouts (COSE / Concentric / Circle).
  - Search bar to highlight and zoom to any advocate, judge, or case node.
  - Node click inspector panel displaying multi-hop citations and connected parties.
- **Daily Cause List Dashboard**:
  - Live courtroom listings with courtroom filters (`Court 1`, `Court 2`), item numbers, advocate names, and clash badges.
- **Hybrid GraphRAG Search Portal**:
  - Interactive search bar returning grounded legal context, statutory references, cited precedents, and direct order text excerpts.
- **Community Clusters Explorer**:
  - Grid view of thematic legal clusters with community metrics and top statutory sections.

### 3. REST API & CLI Integration
- REST API:
  - `GET /api/graph/communities`: Return detected communities and metrics.
  - `GET /ui`: Serve SPA interface.
- CLI:
  - `python projects/LawNidhi/cli.py graph-communities [--min-size 3]`
