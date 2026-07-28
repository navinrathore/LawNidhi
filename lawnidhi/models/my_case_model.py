from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum

class CaseStatus(str, Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    DISPOSED = "DISPOSED"
    CLOSED = "CLOSED"

class MyCaseModel(BaseModel):
    """Represents a case in the counsel's portfolio."""
    id: Optional[int] = None
    case_number: str
    case_year: str
    case_title: Optional[str] = None
    status: CaseStatus = CaseStatus.NEW
    primary_counsel: Optional[str] = None
    associate_counsel: Optional[str] = None
    applicant: Optional[str] = None
    respondent: Optional[str] = None
    requester_department: Optional[str] = None
    requester_name: Optional[str] = None
    diary_number: Optional[str] = None
    date_assigned: Optional[date] = None
    date_closed: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def display_case_id(self) -> str:
        return f"{self.case_number}/{self.case_year}"

    def display_summary(self) -> str:
        title = self.case_title or "Untitled"
        return f"[{self.status.value}] {self.display_case_id()} - {title}"
