"""order_parser.py: Extract structured triplets, header metadata, and statutes from NGT order PDFs."""
from __future__ import annotations
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import pdfplumber

from lawnidhi.graph.schema import (
    OrderExtractionResult,
    StatuteReference,
    PrecedentCitation,
    JudicialDirection,
    normalize_entity_id
)
from lawnidhi.parsers.ngt.statute_parser import StatuteParser
from lawnidhi.parsers.ngt.cause_list_parser import NGTCauseListParser


class NGTOrderParser:
    """Extracts metadata, coram, statutes, and precedent references from judicial order PDFs."""

    # Regex for standard Supreme Court & High Court reporter citations
    CITATION_PATTERNS = [
        # "Vellore Citizens Welfare Forum v. Union of India (1996) 5 SCC 647"
        r"([A-Z][A-Za-z\s\.,&'\(\)]+?\s+(?:v\.|vs\.?|Versus)\s+[A-Z][A-Za-z\s\.,&'\(\)]+?)[,\s]+(?:\(?(\d{4})\)?\s*(\d+\s*(?:SCC|SCR|AIR|Scale)\s*\d+))",
        # "(2020) 10 SCC 550"
        r"(?:\(?(\d{4})\)?\s*(\d+\s*SCC\s*\d+))",
    ]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text pages from an NGT Order PDF."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

        return "\n\n".join(full_text)

    def parse_header(self, text: str) -> Dict[str, Any]:
        """Extract coram judges, case number, court number, and order date from the header."""
        header_sample = text[:3500]
        # Normalize unicode quotes and spaces
        norm_header = header_sample.replace("’", "'").replace("`", "'").replace("\r", "\n")

        # 1. Coram / Judges
        coram_judges = []
        coram_block_match = re.search(r"(?i)CORAM\s*:\s*(.*?)(?=\n\s*(?:Applicant|Appellant|Respondent|ORDER|Counsel|Advocate|1\.|\bIn this\b))", norm_header, re.DOTALL)
        if coram_block_match:
            block_text = coram_block_match.group(1)
            for line in block_text.split("\n"):
                line_clean = line.strip()
                if "HON'BLE" in line_clean.upper() or "JUSTICE" in line_clean.upper() or "DR." in line_clean.upper():
                    # Strip role designations (CHAIRPERSON, JUDICIAL MEMBER, EXPERT MEMBER)
                    line_clean = re.sub(r"(?i),?\s*(?:CHAIRPERSON|JUDICIAL\s+MEMBER|EXPERT\s+MEMBER)", "", line_clean)
                    clean_j = NGTCauseListParser._clean_counsel_name(line_clean)
                    if clean_j and len(clean_j) > 3 and clean_j not in coram_judges:
                        coram_judges.append(clean_j)

        if not coram_judges:
            # Fallback regex
            coram_matches = re.findall(
                r"(?i)(?:hon['’]ble\s+(?:mr\.|mrs\.|ms\.|dr\.)?\s*(?:justice\s+)?([A-Z\s\.]+?)(?:,\s*chairperson|,\s*judicial\s+member|,\s*expert\s+member|\n))",
                norm_header
            )
            for jm in coram_matches:
                clean_j = NGTCauseListParser._clean_counsel_name(jm)
                if clean_j and len(clean_j) > 3 and clean_j not in coram_judges:
                    coram_judges.append(clean_j)

        # 2. Case Number
        case_no_match = re.search(
            r"(?i)(?:original\s+application|o\.?a\.?|appeal|execution\s+application|review\s+application)\s+(?:no\.?\s*)?([0-9]+\s*(?:\([^\)]+\))?\s*/\s*[0-9]{4})",
            norm_header
        )
        case_name = case_no_match.group(0).strip() if case_no_match else "Unknown NGT Case"

        # 3. Order Date
        date_match = re.search(
            r"(?i)(?:date\s+of\s+hearing|date\s+of\s+order|dated\s*:\s*|dated\s+this\s+)\s*[:\s]*([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+[0-9]{4}|[0-9]{1,2}[-\/\.][0-9]{1,2}[-\/\.][0-9]{4})",
            norm_header
        )
        order_date = None
        if date_match:
            raw_date = date_match.group(1).strip()
            order_date = self._parse_date_string(raw_date)

        # 4. Court Number
        court_match = re.search(r"(?i)court\s+no\.?\s*([0-9]+)", norm_header)
        court_no = f"Court {court_match.group(1)}" if court_match else "Court 1"

        return {
            "case_name": case_name,
            "coram_judges": coram_judges,
            "order_date": order_date,
            "court_number": court_no,
        }

    def _parse_date_string(self, raw_date: str) -> Optional[str]:
        """Convert various court date formats to standard ISO YYYY-MM-DD."""
        clean = re.sub(r"(st|nd|rd|th)", "", raw_date).strip()
        formats = [
            "%d %B %Y", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
            "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue
        return None

    def extract_precedents(self, text: str) -> List[PrecedentCitation]:
        """Deterministic regex extractor for landmark Supreme Court / High Court citations."""
        citations: List[PrecedentCitation] = []
        named_citations = {}
        bare_citations = []

        # 1. First pass: extract named case citations (e.g. "Vellore Citizens... (1996) 5 SCC 647")
        pattern_named = r"([A-Z][A-Za-z\s\.,&'\(\)]+?\s+(?:v\.|vs\.?|Versus)\s+[A-Z][A-Za-z\s\.,&'\(\)]+?)[,\s]+(?:\(?(\d{4})\)?\s*(\d+\s*(?:SCC|SCR|AIR|Scale)\s*\d+))"
        for match in re.finditer(pattern_named, text):
            title = match.group(1).replace("\n", " ").strip(" ,.")
            year = int(match.group(2)) if match.group(2) else None
            reporter = match.group(3).strip() if match.group(3) else None
            title_clean = re.sub(r"\s+", " ", title)
            if len(title_clean) > 3 and not title_clean.startswith("Landmark"):
                named_citations[reporter or title_clean] = PrecedentCitation(
                    case_title=title_clean,
                    citation=reporter,
                    year=year,
                    court="Supreme Court of India" if "SCC" in str(reporter) or "SCR" in str(reporter) else "High Court"
                )

        # 2. Second pass: extract standalone SCC citations if not already captured
        pattern_bare = r"(?:\(?(\d{4})\)?\s*(\d+\s*SCC\s*\d+))"
        for match in re.finditer(pattern_bare, text):
            year = int(match.group(1)) if match.group(1) else None
            reporter = match.group(2).strip() if match.group(2) else None
            if reporter and reporter not in named_citations:
                bare_citations.append(PrecedentCitation(
                    case_title=f"Supreme Court Judgment ({reporter})",
                    citation=reporter,
                    year=year,
                    court="Supreme Court of India"
                ))

        # Combine named citations first, then distinct bare citations
        return list(named_citations.values()) + bare_citations

    def parse_order(self, pdf_path: str) -> OrderExtractionResult:
        """Complete pipeline: Extract text, parse header, match statutes, and identify citations."""
        text = self.extract_text_from_pdf(pdf_path)
        header = self.parse_header(text)

        # 1. Extract statutory references
        statutes = StatuteParser.extract_statutes(text)

        # 2. Extract precedent citations
        precedents = self.extract_precedents(text)

        # 3. Create canonical case ID
        case_id = normalize_entity_id("CASE", header["case_name"])

        return OrderExtractionResult(
            case_id=case_id,
            case_name=header["case_name"],
            order_date=header["order_date"],
            court_number=header["court_number"],
            bench_judges=header["coram_judges"],
            invoked_statutes=statutes,
            cited_precedents=precedents,
            directions=[]
        )
