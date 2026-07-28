import re
import pdfplumber
from typing import List, Optional
from datetime import datetime
from lawnidhi.parsers.base import BaseParser
from lawnidhi.models.core import ScheduleModel, CaseModel, PartyModel, CounselModel

class NGTCauseListParser(BaseParser):
    
    def _parse_date(self, text: str) -> Optional[datetime.date]:
        match = re.search(r'Date\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            try:
                date_str = re.sub(r'(st|nd|rd|th)', '', date_str)
                return datetime.strptime(date_str, "%d %B, %Y").date()
            except ValueError:
                pass
        return datetime.now().date()
        
    def _parse_judges(self, text: str) -> str:
        judges = []
        for line in text.split('\n'):
            if "HON’BLE" in line or "HON'BLE" in line:
                judges.append(line.replace("HON’BLE", "").replace("HON'BLE", "").strip())
        return " & ".join(judges)

    def _split_case_num(self, case_text: str):
        match = re.search(r'(.+)/(\d{4})', case_text)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return case_text.strip(), ""

    def parse(self, filepath: str) -> ScheduleModel:
        cases: List[CaseModel] = []
        date_obj = None
        judge_name = ""
        court_no = ""
        
        with pdfplumber.open(filepath) as pdf:
            first_page_text = pdf.pages[0].extract_text()
            date_obj = self._parse_date(first_page_text)
            judge_name = self._parse_judges(first_page_text)
            
            list_type = "Final"
            if "ADVANCE" in first_page_text.upper():
                list_type = "Advance"
            elif "TENTATIVE" in first_page_text.upper():
                list_type = "Tentative"
            elif "SUPPLEMENTARY" in first_page_text.upper():
                list_type = "Supplementary"
            
            c_match = re.search(r'COURT NO\.\s*(\d+)', first_page_text, re.IGNORECASE)
            if c_match:
                court_no = c_match.group(1)

            current_case = None

            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if len(row) < 4:
                            continue
                        
                        s_no = row[0]
                        case_no = row[1] or ""
                        parties = row[2] or ""
                        counsel = row[3] or ""
                        
                        if s_no and s_no != 'S.NO.' and re.match(r'^\d+\.$', str(s_no).strip()):
                            if current_case:
                                self._finalize_case(current_case, cases)
                            
                            cnum, cyear = self._split_case_num(case_no)
                            current_case = {
                                's_no': s_no.strip(),
                                'case_number': cnum,
                                'case_year': cyear,
                                'raw_parties': parties.strip(),
                                'raw_counsel': counsel.strip()
                            }
                        elif current_case and not s_no:
                            if case_no:
                                current_case['case_number'] += " " + case_no.strip()
                            if parties:
                                current_case['raw_parties'] += " " + parties.strip()
                            if counsel:
                                current_case['raw_counsel'] += " " + counsel.strip()
                                
            if current_case:
                self._finalize_case(current_case, cases)
                
        for c in cases:
            if c.case_year == "" and "/" in c.case_number:
                cnum, cyear = self._split_case_num(c.case_number)
                c.case_number = cnum
                c.case_year = cyear

        return ScheduleModel(
            date=date_obj,
            judge_name=judge_name,
            court_no=court_no,
            list_type=list_type,
            cases=cases
        )

    def _finalize_case(self, current_case, cases_list):
        parties_text = current_case['raw_parties']
        applicants = []
        respondents = []
        
        if ' Vs ' in parties_text or '\nVs\n' in parties_text or '\nVs ' in parties_text or ' Vs' in parties_text:
            parts = re.split(r'\s+Vs\s+', parties_text.replace('\n', ' '), maxsplit=1)
            if len(parts) == 1:
                parts = parties_text.split('Vs')
            app = parts[0].strip()
            res = parts[1].strip() if len(parts) > 1 else ""
            applicants.append(PartyModel(name=app, role="Applicant"))
            respondents.append(PartyModel(name=res, role="Respondent"))
        else:
            applicants.append(PartyModel(name=parties_text.strip(), role="Applicant"))
            
        counsels = []
        for c_text in current_case['raw_counsel'].replace('\n', ' ').split(','):
            if c_text.strip():
                counsels.append(CounselModel(name=c_text.strip()))
                
        cases_list.append(CaseModel(
            case_number=current_case['case_number'].replace('\n', ' ').strip(),
            case_year=current_case['case_year'],
            applicants=applicants,
            respondents=respondents,
            counsels=counsels
        ))

if __name__ == "__main__":
    parser = NGTCauseListParser()
    schedule = parser.parse("/home/navin/work/AI/LawNidhi/data/cause_list_sample.pdf")
    print(f"Schedule Date: {schedule.date}")
    print(f"Judges: {schedule.judge_name}")
    print(f"Total Cases: {len(schedule.cases)}")
    for i, c in enumerate(schedule.cases[:3]):
        print(f"\nCase {i+1}: {c.case_number}/{c.case_year}")
        print(f"Applicants: {[a.name for a in c.applicants]}")
        print(f"Respondents: {[r.name for r in c.respondents]}")
        print(f"Counsels: {[coun.name for coun in c.counsels]}")
