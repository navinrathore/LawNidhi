from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class CounselModel(BaseModel):
    name: str

class PartyModel(BaseModel):
    name: str
    role: str # 'Applicant' or 'Respondent'

class CaseModel(BaseModel):
    case_number: Optional[str] = None
    case_year: Optional[str] = None
    diary_number: Optional[str] = None
    applicants: List[PartyModel] = Field(default_factory=list)
    respondents: List[PartyModel] = Field(default_factory=list)
    counsels: List[CounselModel] = Field(default_factory=list)
    
class ScheduleModel(BaseModel):
    date: date
    judge_name: str
    list_type: str = "Final"
    cases: List[CaseModel] = Field(default_factory=list)
    court_no: Optional[str] = None
