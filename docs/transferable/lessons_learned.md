# Lessons Learned & Transferable Knowledge

## 1. Unstructured PDF Parsing is Highly Fragile
Using tools like `pdfplumber` for legal PDFs reveals that "tables" in PDFs are often just floating text blocks aligned visually, rather than true structural elements.
**Transferable Insight:** Never rely solely on grid-based table extraction for scanned or old PDFs. Always implement a secondary text-based Regex parsing fallback to catch data that isn't cleanly enclosed in table borders.

## 2. SQLite Concurrency Limits
While SQLite is excellent for portable desktop applications, batch operations (like `sync-cause-lists`) can cause `database is locked` errors.
**Transferable Insight:** When doing heavy batch inserts in SQLite:
1. Enable WAL (Write-Ahead Logging) mode: `PRAGMA journal_mode=WAL;`.
2. Batch your `INSERT` statements into a single transaction rather than committing after every row.

## 3. Dynamic RAG Top-K
In legal domains, a single relevant sentence might require the context of the entire preceding paragraph to make sense.
**Transferable Insight:** Don't just retrieve the Top-K chunks. Implement **Context Windowing** (retrieving Chunk N, plus Chunk N-1 and Chunk N+1) to ensure the LLM has enough surrounding text to understand isolated legal clauses.
