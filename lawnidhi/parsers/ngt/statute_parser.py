"""statute_parser.py: Deterministic, zero-token statutory section and act extractor for Indian environmental jurisprudence."""
from __future__ import annotations
import re
from typing import List, Set, Tuple
from lawnidhi.graph.schema import StatuteReference


class StatuteParser:
    """Deterministic regex-based extractor for statutory acts and provisions."""

    # Canonical mapping for common variations
    CANONICAL_ACTS = {
        "ngt": "National Green Tribunal Act, 2010",
        "national green tribunal": "National Green Tribunal Act, 2010",
        "national green tribunal act": "National Green Tribunal Act, 2010",
        "water": "Water (Prevention and Control of Pollution) Act, 1974",
        "water act": "Water (Prevention and Control of Pollution) Act, 1974",
        "water (prevention and control of pollution)": "Water (Prevention and Control of Pollution) Act, 1974",
        "water (prevention and control of pollution) act": "Water (Prevention and Control of Pollution) Act, 1974",
        "air": "Air (Prevention and Control of Pollution) Act, 1981",
        "air act": "Air (Prevention and Control of Pollution) Act, 1981",
        "air (prevention and control of pollution)": "Air (Prevention and Control of Pollution) Act, 1981",
        "air (prevention and control of pollution) act": "Air (Prevention and Control of Pollution) Act, 1981",
        "ep": "Environment (Protection) Act, 1986",
        "ep act": "Environment (Protection) Act, 1986",
        "epa": "Environment (Protection) Act, 1986",
        "environment (protection)": "Environment (Protection) Act, 1986",
        "environment (protection) act": "Environment (Protection) Act, 1986",
        "environment protection act": "Environment (Protection) Act, 1986",
        "forest conservation": "Forest (Conservation) Act, 1980",
        "forest (conservation)": "Forest (Conservation) Act, 1980",
        "forest (conservation) act": "Forest (Conservation) Act, 1980",
        "forest act": "Indian Forest Act, 1927",
        "indian forest act": "Indian Forest Act, 1927",
        "biodiversity": "Biological Diversity Act, 2002",
        "biological diversity": "Biological Diversity Act, 2002",
        "biological diversity act": "Biological Diversity Act, 2002",
        "public liability insurance": "Public Liability Insurance Act, 1991",
        "public liability insurance act": "Public Liability Insurance Act, 1991",
        "solid waste management": "Solid Waste Management Rules, 2016",
        "solid waste management rules": "Solid Waste Management Rules, 2016",
        "hazardous waste": "Hazardous and Other Wastes Rules, 2016",
        "bio-medical waste": "Bio-Medical Waste Management Rules, 2016",
        "plastic waste": "Plastic Waste Management Rules, 2016",
        "e-waste": "E-Waste (Management) Rules, 2016",
        "eia notification": "EIA Notification, 2006",
        "crz notification": "CRZ Notification, 2011",
        "constitution": "Constitution of India",
        "constitution of india": "Constitution of India",
    }

    # Targeted patterns for high precision
    EXPLICIT_PATTERNS = [
        # "Section 14 of the National Green Tribunal Act, 2010"
        r"(?i)\b(?:section|sec\.?)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\s+(?:of\s+(?:the\s+)?)?((?:national\s+green\s+tribunal|water\s+(?:\(prevention\s+and\s+control\s+of\s+pollution\)\s+)?|air\s+(?:\(prevention\s+and\s+control\s+of\s+pollution\)\s+)?|environment\s+(?:\(protection\)\s+)?|forest\s+(?:\(conservation\)\s+)?|biological\s+diversity|public\s+liability\s+insurance)\s*act(?:,?\s*\d{4})?)",
        
        # "Section 33A, Water Act, 1974" or "Section 21 Air Act"
        r"(?i)\b(?:section|sec\.?)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)[,\s]+(?:of\s+)?((?:ngt|water|air|ep|epa)\s+act)",

        # "under Section 14/15/18/19/20 of the NGT Act"
        r"(?i)\b(?:under\s+section|u/s)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\s+(?:of\s+(?:the\s+)?)?((?:ngt|water|air|ep|epa)\s+act|national\s+green\s+tribunal\s+act)",

        # Article 21/48A/51A of Constitution
        r"(?i)\b(?:article|art\.?)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\s+(?:of\s+(?:the\s+)?)?(constitution(?:\s+of\s+india)?)",

        # "Rule X of Solid Waste Management Rules / Bio-Medical Waste / Plastic Waste"
        r"(?i)\b(?:rule|paragraph|para|clause)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\s+(?:of\s+(?:the\s+)?)?((?:solid\s+waste\s+management|hazardous\s+(?:and\s+other\s+)?waste|bio-medical\s+waste|plastic\s+waste|e-waste)\s*rules(?:,?\s*\d{4})?)",

        # Generic Section X of Y Act, Year
        r"(?i)\b(?:section|sec\.?)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\s+(?:of\s+(?:the\s+)?)?([A-Z][A-Za-z\s,\(\)\-]{3,50}Act,?\s*\d{4})",

        # Generic Rule X of Y Rules, Year / Notification
        r"(?i)\b(?:rule|paragraph|para|clause)\s+([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\s+(?:of\s+(?:the\s+)?)?([A-Z][A-Za-z\s,\(\)\-]{3,50}(?:Rules|Notification),?\s*\d{4})",
    ]

    @classmethod
    def _normalize_act_name(cls, raw_act: str) -> str:
        """Map raw act name string to canonical Act title."""
        clean = raw_act.lower().replace("\n", " ").strip(" ,.")
        clean = re.sub(r"\s+", " ", clean)
        clean = re.sub(r"^(?:the\s+)", "", clean)

        for key, canonical in cls.CANONICAL_ACTS.items():
            if key in clean:
                return canonical

        # Fallback capitalization for unrecognized acts
        return raw_act.strip(" ,.").title()

    @classmethod
    def extract_statutes(cls, text: str) -> List[StatuteReference]:
        """Extract all statutory provisions from judgment or order text."""
        if not text:
            return []

        results: List[StatuteReference] = []
        seen: Set[Tuple[str, str]] = set()

        # 1. Multi-section compound matcher: "Sections 14, 15 and 18 of NGT Act" or "Section 14 and Section 15 of NGT Act"
        compound_pattern = r"(?i)\b(?:sections?|sec\.?|articles?|art\.?|rules?)\s+([0-9A-Za-z,\(\)\s\/]+?(?:\band\b|\b&\b|\bread\s+with\b)?[0-9A-Za-z,\(\)\s\/]*?)\s+(?:of\s+(?:the\s+)?)?((?:national\s+green\s+tribunal|water\s+(?:\(prevention\s+and\s+control\s+of\s+pollution\)\s+)?|air\s+(?:\(prevention\s+and\s+control\s+of\s+pollution\)\s+)?|environment\s+(?:\(protection\)\s+)?|forest\s+(?:\(conservation\)\s+)?|biological\s+diversity|public\s+liability\s+insurance|ngt|water|air|ep|epa)\s*act(?:,?\s*\d{4})?|constitution(?:\s+of\s+india)?|(?:solid\s+waste\s+management|hazardous\s+(?:and\s+other\s+)?waste|bio-medical\s+waste|plastic\s+waste|e-waste)\s*rules(?:,?\s*\d{4})?)"
        
        for match in re.finditer(compound_pattern, text):
            raw_secs = match.group(1).strip()
            raw_act = match.group(2).strip()
            canonical_act = cls._normalize_act_name(raw_act)
            raw_match = match.group(0).strip()

            # Split individual section numbers
            sec_tokens = re.findall(r"\b([0-9]+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\b", raw_secs)
            for sec in sec_tokens:
                sec_clean = sec.strip().upper()
                key = (canonical_act.lower(), sec_clean.lower())
                if key not in seen:
                    seen.add(key)
                    results.append(StatuteReference(
                        act_name=canonical_act,
                        section=sec_clean,
                        raw_match=raw_match
                    ))

        # 2. Standard explicit single-pattern matchers
        for pattern in cls.EXPLICIT_PATTERNS:
            for match in re.finditer(pattern, text):
                sec = match.group(1).strip().upper()
                raw_act = match.group(2).strip()
                canonical_act = cls._normalize_act_name(raw_act)
                raw_match = match.group(0).strip()

                key = (canonical_act.lower(), sec.lower())
                if key not in seen:
                    seen.add(key)
                    results.append(StatuteReference(
                        act_name=canonical_act,
                        section=sec,
                        raw_match=raw_match
                    ))

        # Sort by Act name and Section for deterministic output
        results.sort(key=lambda x: (x.act_name, x.section))
        return results
