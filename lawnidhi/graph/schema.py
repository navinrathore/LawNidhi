"""schema.py: Strongly typed Pydantic models for Legal Knowledge Graph."""
from __future__ import annotations
import json
import re
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field


EntityType = Literal[
    "CASE",
    "HEARING",
    "JUDGE",
    "BENCH",
    "COUNSEL",
    "PARTY",
    "STATUTE",
    "SECTION",
    "ORDER",
    "DIRECTION",
    "PENALTY"
]

RelationType = Literal[
    "LISTED_AT",
    "HEARD_AT",
    "PRESIDED_BY",
    "HELD_IN",
    "REPRESENTS",
    "APPEARED_IN",
    "PARTY_TO",
    "INVOKES_STATUTE",
    "CITES_PRECEDENT",
    "ISSUED_DIRECTION",
    "IMPOSED_PENALTY",
    "CONTAINS_ORDER",
    "FOLLOWS_HEARING"
]


def normalize_hearing_id(hearing_date: str, court_no: str, list_type: str = "Final") -> str:
    """Helper to create a normalized ID for a specific hearing session.
    
    Example:
        normalize_hearing_id("2025-03-14", "Court 1", "Final") -> "hearing_2025_03_14_court_1_final"
    """
    clean_date = str(hearing_date).replace("-", "_").strip()
    clean_court = re.sub(r"[^\w]", "_", court_no.lower()).strip("_")
    clean_type = re.sub(r"[^\w]", "_", list_type.lower()).strip("_")
    return f"hearing_{clean_date}_{clean_court}_{clean_type}"


def normalize_entity_id(entity_type: str, raw_name: str) -> str:
    """Helper to create a deterministic, normalized entity ID.
    
    Example:
        normalize_entity_id("CASE", "OA 83/2025") -> "case_oa_83_2025"
        normalize_entity_id("COUNSEL", "Adv. Sanjay Upadhyay") -> "counsel_sanjay_upadhyay"
        normalize_entity_id("JUDGE", "Hon'ble Justice Prakash Shrivastava") -> "judge_prakash_shrivastava"
    """
    clean_type = entity_type.lower().strip()
    clean_name = raw_name.lower().strip()
    # Strip any sequence of leading honorifics/titles
    clean_name = re.sub(r"^(?:(?:adv\.|advocate|justice|hon'ble|mr\.|mrs\.|ms\.|shri|smt\.)\s+)+", "", clean_name)
    clean_name = re.sub(r"[^\w\s-]", "_", clean_name)
    clean_name = re.sub(r"[\s_]+", "_", clean_name).strip("_")
    return f"{clean_type}_{clean_name}"


class LegalEntity(BaseModel):
    """Represents a discrete entity node in the legal knowledge graph."""
    id: str = Field(description="Unique normalized entity ID (e.g. 'case_oa_83_2025')")
    name: str = Field(description="Display/Canonical name of the entity")
    entity_type: EntityType = Field(description="Category of the legal entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-values")

    def properties_json(self) -> str:
        """Serialize properties dictionary to JSON string for database storage."""
        return json.dumps(self.properties, ensure_ascii=False)

    @classmethod
    def create(
        cls,
        name: str,
        entity_type: EntityType,
        custom_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> LegalEntity:
        """Factory method to automatically construct a normalized entity."""
        ent_id = custom_id or normalize_entity_id(entity_type, name)
        return cls(
            id=ent_id,
            name=name.strip(),
            entity_type=entity_type,
            properties=properties or {}
        )


class LegalRelation(BaseModel):
    """Represents a directed semantic relationship edge between two entities."""
    source_id: str = Field(description="ID of the source LegalEntity node")
    relation_type: RelationType = Field(description="Relationship label")
    target_id: str = Field(description="ID of the target LegalEntity node")
    weight: float = Field(default=1.0, description="Confidence or frequency weight (0.0 - 1.0)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")

    def properties_json(self) -> str:
        """Serialize properties dictionary to JSON string for database storage."""
        return json.dumps(self.properties, ensure_ascii=False)


class GraphExtraction(BaseModel):
    """Container schema for extracting multiple entities and relations from a text block."""
    entities: List[LegalEntity] = Field(default_factory=list, description="Extracted entity nodes")
    relationships: List[LegalRelation] = Field(default_factory=list, description="Extracted semantic edges")
