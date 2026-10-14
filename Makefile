# ==============================================================================
# ⚖️ NyayaGraph (न्यायGraph) Makefile
# Quick developer shortcuts for CLI, Knowledge Graph, and RAG workflows.
# ==============================================================================

.PHONY: help stats sync sync-orders sync-all board communities serve test rag ask clashes timeline db-stats clean

# Detect Python interpreter (prefer miniconda3 / active venv)
ifeq ($(origin VIRTUAL_ENV), undefined)
    ifeq ($(wildcard /home/navin/work/packages/miniconda3/bin/python),)
        PYTHON ?= python3
    else
        PYTHON ?= /home/navin/work/packages/miniconda3/bin/python
    endif
else
    PYTHON ?= $(VIRTUAL_ENV)/bin/python
endif

export PYTHONPATH := .:$(PYTHONPATH)

help: ## Show this help message
	@echo ""
	@echo "⚖️  NyayaGraph Makefile Commands"
	@echo "==============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Tip: You can also use the shortform script directly: ./ng <command>"
	@echo ""

# ------------------------------------------------------------------------------
# 🏛️ Knowledge Graph Commands
# ------------------------------------------------------------------------------

stats: ## View Knowledge Graph entity counts and topology (nodes/edges)
	@$(PYTHON) cli.py graph-stats

board: ## View daily courtroom cause list board (today/tomorrow)
	@$(PYTHON) cli.py graph-daily-board

communities: ## Detect and display macro-thematic legal graph clusters
	@$(PYTHON) cli.py graph-communities

sync: ## Ingest all downloaded cause lists into the Knowledge Graph
	@$(PYTHON) cli.py graph-sync

sync-orders: ## Batch extract and ingest order PDFs into Knowledge Graph
	@$(PYTHON) cli.py graph-sync-orders

sync-all: sync sync-orders ## Run full ingestion: cause lists + order PDFs

timeline: ## View hearing timeline for a case (Usage: make timeline case=83/2025)
	@if [ -z "$(case)" ]; then echo "Error: specify case=<number/year>, e.g., make timeline case=83/2025"; exit 1; fi
	@$(PYTHON) cli.py graph-timeline $(case)

clashes: ## Detect courtroom clashes for counsel (Usage: make clashes counsel="Hemlata Singh")
	@$(PYTHON) cli.py graph-counsel-clashes "$(counsel)"

# ------------------------------------------------------------------------------
# 🧠 Hybrid GraphRAG & Agentic Co-Counsel
# ------------------------------------------------------------------------------

rag: ## Run Hybrid GraphRAG query (Usage: make rag q="water pollution tanneries")
	@if [ -z "$(q)" ]; then echo "Error: specify q=\"<query>\", e.g., make rag q=\"water pollution\""; exit 1; fi
	@$(PYTHON) cli.py graph-rag "$(q)"

ask: ## Autonomous ReAct Legal Co-Counsel (Usage: make ask q="Prepare brief for OA 985/2019")
	@if [ -z "$(q)" ]; then echo "Error: specify q=\"<query>\", e.g., make ask q=\"Prepare brief for OA 985/2019\""; exit 1; fi
	@$(PYTHON) cli.py ask "$(q)"

# ------------------------------------------------------------------------------
# 🚀 Server & Testing
# ------------------------------------------------------------------------------

serve: ## Start FastAPI REST server and Swagger docs (:8000)
	@$(PYTHON) cli.py serve --host 127.0.0.1 --port 8000

test: ## Run the full 45-test pytest suite
	@$(PYTHON) -m pytest tests/ -v

db-stats: ## View SQLite relational docket database summary
	@$(PYTHON) cli.py db-stats

clean: ## Clean Python cache files
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
