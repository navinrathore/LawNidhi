import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "lawnidhi.db")

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Cases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT,
        case_year TEXT,
        diary_number TEXT UNIQUE
    )
    ''')
    
    # Create Parties table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        name TEXT,
        role TEXT,
        FOREIGN KEY (case_id) REFERENCES cases (id)
    )
    ''')
    
    # Create Counsels table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS counsels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    ''')
    
    # Create Case_Counsels mapping
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS case_counsels (
        case_id INTEGER,
        counsel_id INTEGER,
        FOREIGN KEY (case_id) REFERENCES cases (id),
        FOREIGN KEY (counsel_id) REFERENCES counsels (id),
        PRIMARY KEY (case_id, counsel_id)
    )
    ''')
    
    # Create Schedules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_date DATE,
        court_no TEXT,
        judge_name TEXT,
        list_type TEXT,
        UNIQUE(schedule_date, court_no, list_type)
    )
    ''')
    
    # Create Schedule_Cases mapping
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule_cases (
        schedule_id INTEGER,
        case_id INTEGER,
        item_number INTEGER,
        FOREIGN KEY (schedule_id) REFERENCES schedules (id),
        FOREIGN KEY (case_id) REFERENCES cases (id),
        PRIMARY KEY (schedule_id, case_id)
    )
    ''')
    
    # Create cause_lists tracking table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cause_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        list_type TEXT,
        court_no TEXT,
        file_path TEXT,
        source_url TEXT,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, list_type, court_no)
    )
    ''')
    
    conn.commit()
    conn.close()

    # Create the my_cases portfolio table
    from lawnidhi.db.my_cases_schema import create_my_cases_table
    create_my_cases_table()

if __name__ == "__main__":
    create_tables()
