# Phase 1 Validation & Test Plan: Legal Ontology & Graph Engine

## Verification Criteria

To validate Phase 1 completion, the following automated tests must pass without errors:

| Test Case | Description | Verification Method |
| :--- | :--- | :--- |
| **`test_store_init`** | Verifies Kùzu DB directory creation and schema table creation. | `pytest projects/LawNidhi/tests/test_graph_store.py::test_store_init` |
| **`test_insert_and_get_entity`** | Inserts entities and fetches them by ID. | `pytest projects/LawNidhi/tests/test_graph_store.py::test_insert_and_get_entity` |
| **`test_insert_and_traverse_relation`** | Creates relationships between nodes and traverses 1-hop edges. | `pytest projects/LawNidhi/tests/test_graph_store.py::test_insert_and_traverse_relation` |
| **`test_multi_hop_precedents`** | Inserts a Case $\rightarrow$ cites $\rightarrow$ PriorCase and Case $\rightarrow$ invokes $\rightarrow$ Statute and runs 2-hop traversal. | `pytest projects/LawNidhi/tests/test_graph_store.py::test_multi_hop_precedents` |
| **`test_graph_stats`** | Verifies entity count, relationship count, and category breakdown. | `pytest projects/LawNidhi/tests/test_graph_store.py::test_graph_stats` |

## Execution Command
```bash
python3 -m pytest projects/LawNidhi/tests/test_graph_store.py -v
```
