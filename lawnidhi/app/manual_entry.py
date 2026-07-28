from typing import List
from datetime import datetime
from lawnidhi.models.core import ScheduleModel, CaseModel, PartyModel, CounselModel
from lawnidhi.db.ingest import ingest_schedule

def insert_manual_case(
    date_str: str, 
    judge_name: str, 
    court_no: str, 
    case_number: str, 
    case_year: str, 
    applicants: List[str], 
    respondents: List[str], 
    counsels: List[str],
    diary_number: str = None
) -> int:
    """
    Creates a ScheduleModel directly from primitive Python types and ingests it into the database.
    This demonstrates the framework's capability to accept inputs from web forms, chatbots, or manual text entry.
    """
    
    app_models = [PartyModel(name=a, role="Applicant") for a in applicants]
    res_models = [PartyModel(name=r, role="Respondent") for r in respondents]
    counsel_models = [CounselModel(name=c) for c in counsels]
    
    case_model = CaseModel(
        case_number=case_number,
        case_year=case_year,
        diary_number=diary_number,
        applicants=app_models,
        respondents=res_models,
        counsels=counsel_models
    )
    
    schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    schedule_model = ScheduleModel(
        date=schedule_date,
        judge_name=judge_name,
        court_no=court_no,
        cases=[case_model]
    )
    
    # Delegate to the exact same DB ingestion logic used by the PDF Extractors.
    schedule_id = ingest_schedule(schedule_model)
    return schedule_id

if __name__ == "__main__":
    print("Inserting a hypothetical case from a Chat Interface...")
    sched_id = insert_manual_case(
        date_str="2026-04-10",
        judge_name="HON'BLE BOT",
        court_no="Test Court",
        case_number="MANUAL CASE NO. 99",
        case_year="2026",
        applicants=["Save The Trees Foundation"],
        respondents=["Deforestation Corp"],
        counsels=["NAVIN "],
        diary_number="D99992026"
    )
    print(f"Successfully inserted manual case. Assigned Schedule ID: {sched_id}")
    
    # Verify we can generate an invoice for the newly ingested manual counsel
    from lawnidhi.app.reports import generate_counsel_appearance_log
    print("\nVerifying integration by generating Counsel Log for NAVIN SINGH:")
    print(generate_counsel_appearance_log("NAVIN SINGH"))
