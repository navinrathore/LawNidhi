"""synthesizer.py: Provider-agnostic legal intelligence synthesizer adhering to Rule 11 (Supervisory Wrapper)."""
from __future__ import annotations
from typing import Dict, Optional, Any
from lawnidhi.rag.schema import HybridRetrievalResult, RAGAnswer


class LegalSynthesizer:
    """Supervisory synthesizer wrapping deterministic hybrid retrieval."""

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client

    def synthesize(self, result: HybridRetrievalResult) -> RAGAnswer:
        """Synthesize a structured legal answer from grounded hybrid retrieval results."""
        source_cases = list({c.case_name for c in result.text_chunks if c.case_name})
        
        # If an external LLM client is provided, invoke it
        if self.llm_client is not None:
            try:
                system_prompt = (
                    "You are LawNidhi, an authoritative judicial AI assistant. "
                    "Synthesize a clear legal response based exclusively on the provided statutory sections, "
                    "precedents, and judicial order excerpts. Explicitly cite the sources."
                )
                answer_text = self.llm_client.complete(
                    system_prompt=system_prompt,
                    user_prompt=result.formatted_context
                )
                return RAGAnswer(
                    query=result.query,
                    answer=answer_text,
                    source_cases=source_cases,
                    cited_statutes=result.statutory_provisions,
                    cited_precedents=result.precedent_lineage,
                    bench_members=result.bench_judges,
                    retrieval_metadata={"mode": "llm_synthesized", "chunks_count": len(result.text_chunks)}
                )
            except Exception:
                pass  # Fallback to deterministic synthesis

        # Deterministic Grounded Synthesis (Rule 11: $0 token tax)
        answer_lines = [
            f"### Legal Summary for Query: '{result.query}'\n",
        ]

        if result.statutory_provisions:
            answer_lines.append(f"**Applicable Statutes & Sections:** {', '.join(result.statutory_provisions)}")
        if result.precedent_lineage:
            answer_lines.append(f"**Binding Supreme Court Precedents:** {', '.join(result.precedent_lineage[:5])}")
        if result.bench_judges:
            answer_lines.append(f"**Presiding Coram:** {', '.join(result.bench_judges[:3])}")
        if source_cases:
            answer_lines.append(f"**Direct Cases:** {', '.join(source_cases[:3])}")

        if result.text_chunks:
            answer_lines.append("\n**Primary Judicial Findings:**")
            for chunk in result.text_chunks[:2]:
                answer_lines.append(f"- *{chunk.case_name}*: \"{chunk.text[:250]}...\"")
        else:
            answer_lines.append("\nNo directly matching order text passages were found.")

        answer_lines.append("\n*Note: Synthesized via LawNidhi Deterministic Hybrid GraphRAG Engine.*")

        return RAGAnswer(
            query=result.query,
            answer="\n".join(answer_lines),
            source_cases=source_cases,
            cited_statutes=result.statutory_provisions,
            cited_precedents=result.precedent_lineage,
            bench_members=result.bench_judges,
            retrieval_metadata={"mode": "deterministic_grounded", "chunks_count": len(result.text_chunks)}
        )
