"""lawnidhi.agent: Autonomous Agentic Legal Co-Counsel for LawNidhi."""
from lawnidhi.agent.schema import AgentStep, CoCounselResponse, CaseBrief
from lawnidhi.agent.tools import LegalToolRegistry
from lawnidhi.agent.co_counsel import AgenticCoCounsel

__all__ = [
    "AgentStep",
    "CoCounselResponse",
    "CaseBrief",
    "LegalToolRegistry",
    "AgenticCoCounsel",
]
