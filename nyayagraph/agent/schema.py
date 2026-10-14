"""schema.py: Pydantic schemas for Agentic Legal Co-Counsel (ReAct Trajectory & Briefs)."""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    loop_index: int
    thought: str
    action_tool: Optional[str] = None
    action_input: Optional[Any] = None
    observation: Optional[str] = None


class CoCounselResponse(BaseModel):
    query: str
    final_answer: str
    steps: List[AgentStep] = Field(default_factory=list)
    tools_invoked: List[str] = Field(default_factory=list)
    loop_count: int = 0
    execution_time_sec: float = 0.0
    structured_data: Dict[str, Any] = Field(default_factory=dict)


class CaseBrief(BaseModel):
    case_id: str
    case_name: str
    court_number: Optional[str] = None
    order_date: Optional[str] = None
    presiding_coram: List[str] = Field(default_factory=list)
    applicants: List[str] = Field(default_factory=list)
    respondents: List[str] = Field(default_factory=list)
    counsels: List[str] = Field(default_factory=list)
    invoked_statutes: List[str] = Field(default_factory=list)
    cited_precedents: List[str] = Field(default_factory=list)
    case_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    key_findings: str = ""
