"""vector_store.py: In-memory & indexed document store for judicial order text search."""
from __future__ import annotations
import glob
import os
import re
from typing import Dict, List, Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from lawnidhi.parsers.ngt.order_parser import NGTOrderParser
from lawnidhi.rag.schema import TextChunk


class LegalDocumentStore:
    """Indexed document store for semantic & keyword retrieval over judicial orders."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks: List[TextChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._is_indexed = False

    def add_document(
        self,
        doc_id: str,
        case_name: str,
        text: str,
        order_date: Optional[str] = None,
        court_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Chunk and add a single legal document to the in-memory store."""
        if not text or not text.strip():
            return 0

        clean_text = re.sub(r"\s+", " ", text).strip()
        doc_chunks = []
        step = max(50, self.chunk_size - self.chunk_overlap)

        for i in range(0, len(clean_text), step):
            chunk_slice = clean_text[i:i + self.chunk_size].strip()
            if len(chunk_slice) < 50:
                continue

            chunk_id = f"{doc_id}_chunk_{len(self.chunks) + len(doc_chunks)}"
            doc_chunks.append(TextChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                case_name=case_name,
                order_date=order_date,
                court_number=court_number,
                text=chunk_slice,
                metadata=metadata or {}
            ))

        self.chunks.extend(doc_chunks)
        self._is_indexed = False
        return len(doc_chunks)

    def index_directory(self, orders_dir: str) -> int:
        """Scan and chunk all PDF files in the specified orders directory."""
        if not os.path.isdir(orders_dir):
            return 0

        pdf_files = sorted(glob.glob(os.path.join(orders_dir, "*.pdf")))
        parser = NGTOrderParser()
        indexed_docs = 0

        for pdf_path in pdf_files:
            try:
                text = parser.extract_text_from_pdf(pdf_path)
                header = parser.parse_header(text[:2000])
                doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
                case_name = header.get("case_name") or f"Case {doc_id}"

                self.add_document(
                    doc_id=doc_id,
                    case_name=case_name,
                    text=text,
                    order_date=header.get("order_date"),
                    court_number=header.get("court_number"),
                    metadata={"source_file": pdf_path}
                )
                indexed_docs += 1
            except Exception:
                continue

        self.build_index()
        return indexed_docs

    def build_index(self):
        """Fit the TF-IDF vectorizer over all accumulated document chunks."""
        if not self.chunks:
            return

        corpus = [c.text for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=10000
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self._is_indexed = True

    def search(self, query: str, top_k: int = 5) -> List[TextChunk]:
        """Search top-K relevant text chunks given a query string."""
        if not self.chunks:
            return []

        if not self._is_indexed or self.vectorizer is None or self.tfidf_matrix is None:
            self.build_index()

        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score > 0.0:
                chunk = self.chunks[idx].model_copy()
                chunk.score = score
                results.append(chunk)

        return results
