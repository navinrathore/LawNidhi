import sqlite3
from typing import List
from lawnidhi.models.core import ScheduleModel, CaseModel
from lawnidhi.db.schema import DB_PATH

def ingest_schedule(schedule: ScheduleModel):
    """Ingests a fully parsed ScheduleModel into the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # If ingesting a Final schedule, purge any prior Tentative/Advance versions first
        if schedule.list_type == "Final":
            cursor.execute('''SELECT id FROM schedules WHERE schedule_date=? AND court_no=? AND list_type IN ('Tentative', 'Advance')''',
                          (schedule.date, schedule.court_no))
            for old_row in cursor.fetchall():
                old_id = old_row[0]
                cursor.execute('DELETE FROM schedule_cases WHERE schedule_id=?', (old_id,))
                cursor.execute('DELETE FROM schedules WHERE id=?', (old_id,))

        # Check for exact duplicate of the current schedule
        cursor.execute('''SELECT id FROM schedules WHERE schedule_date=? AND court_no=? AND list_type=?''',
                      (schedule.date, schedule.court_no, schedule.list_type))
        row = cursor.fetchone()
        if row:
            schedule_id = row[0]
            cursor.execute('DELETE FROM schedule_cases WHERE schedule_id=?', (schedule_id,))
        else:
            # Insert Schedule
            cursor.execute('''INSERT INTO schedules (schedule_date, court_no, judge_name, list_type) 
                              VALUES (?, ?, ?, ?)''', 
                              (schedule.date, schedule.court_no, schedule.judge_name, schedule.list_type))
            schedule_id = cursor.lastrowid
        
        for item_number, case in enumerate(schedule.cases, start=1):
            cursor.execute('SELECT id FROM cases WHERE case_number=? AND case_year=?', 
                          (case.case_number, case.case_year))
            row = cursor.fetchone()
            
            if row:
                case_id = row[0]
            else:
                cursor.execute('INSERT INTO cases (case_number, case_year, diary_number) VALUES (?, ?, ?)',
                              (case.case_number, case.case_year, case.diary_number))
                case_id = cursor.lastrowid
                
                for app in case.applicants:
                    cursor.execute('INSERT INTO parties (case_id, name, role) VALUES (?, ?, ?)',
                                  (case_id, app.name, app.role))
                for res in case.respondents:
                    cursor.execute('INSERT INTO parties (case_id, name, role) VALUES (?, ?, ?)',
                                  (case_id, res.name, res.role))
            
            cursor.execute('INSERT OR IGNORE INTO schedule_cases (schedule_id, case_id, item_number) VALUES (?, ?, ?)',
                          (schedule_id, case_id, item_number))
            
            for counsel in case.counsels:
                cursor.execute('SELECT id FROM counsels WHERE name=?', (counsel.name,))
                c_row = cursor.fetchone()
                if c_row:
                    counsel_id = c_row[0]
                else:
                    cursor.execute('INSERT INTO counsels (name) VALUES (?)', (counsel.name,))
                    counsel_id = cursor.lastrowid
                
                cursor.execute('INSERT OR IGNORE INTO case_counsels (case_id, counsel_id) VALUES (?, ?)',
                              (case_id, counsel_id))
                              
        conn.commit()
        return schedule_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    from lawnidhi.parsers.ngt.cause_list_parser import NGTCauseListParser
    parser = NGTCauseListParser()
    schedule = parser.parse("/home/navin/work/AI/LawNidhi/data/cause_list_sample.pdf")
    sched_id = ingest_schedule(schedule)
    print(f"Successfully ingested schedule. Schedule ID: {sched_id}. Cases processed: {len(schedule.cases)}")
