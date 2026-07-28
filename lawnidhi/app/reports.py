from typing import List, Dict
from datetime import datetime
from lawnidhi.app.queries import get_cases_by_counsel, get_cases_by_counsel_names
from lawnidhi import config

def generate_counsel_appearance_log(counsel_name: str = None, start_date: str = None, end_date: str = None) -> str:
    """
    Generates a structured work-log/invoice breakdown of a counsel's 
    appearances based on the parsed cause lists in the DB.
    Uses config aliases for flexible name matching.
    Dates should be in 'YYYY-MM-DD' format.
    """
    # Use aliases from config for broader matching
    if counsel_name:
        aliases = config.get_counsel_aliases()
        if aliases and counsel_name in aliases:
            cases = get_cases_by_counsel_names(aliases)
        else:
            cases = get_cases_by_counsel(counsel_name)
        display_name = counsel_name
    else:
        aliases = config.get_counsel_aliases()
        if aliases:
            cases = get_cases_by_counsel_names(aliases)
            display_name = config.get_counsel_name() or aliases[0]
        else:
            return "No counsel name provided and no aliases configured."
    
    if start_date:
        start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        cases = [c for c in cases if datetime.strptime(c['schedule_date'], "%Y-%m-%d").date() >= start_obj]
    if end_date:
        end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        cases = [c for c in cases if datetime.strptime(c['schedule_date'], "%Y-%m-%d").date() <= end_obj]
        
    if not cases:
        return f"No appearances found for {display_name} in the specified timeframe."
        
    report = [f"=================================================="]
    report.append(f"          APPEARANCE LOG & INVOICE DATA           ")
    report.append(f"==================================================")
    report.append(f"Counsel Name: {display_name.upper()}")
    report.append(f"Total Appearances: {len(cases)}")
    report.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"--------------------------------------------------\n")
    
    cases_by_date = {}
    for c in cases:
        date = c['schedule_date']
        if date not in cases_by_date:
            cases_by_date[date] = []
        cases_by_date[date].append(c)
        
    for date, appearances in sorted(cases_by_date.items(), reverse=True):
        report.append(f"DATE: {date}")
        report.append(f"--------------------------------------------------")
        for i, app in enumerate(appearances, 1):
            report.append(f"  {i}. Case No : {app['case_number']}/{app['case_year']}")
            report.append(f"     Court   : Court No. {app['court_no']}")
            report.append(f"     Judges  : {app['judge_name']}")
            report.append("")
            
    report.append("=================== END OF LOG ===================")
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_counsel_appearance_log("SHAHRUKH EJAZ"))
