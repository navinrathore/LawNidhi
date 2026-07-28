import sqlite3
from lawnidhi.db.schema import DB_PATH

def create_my_cases_table():
    """Creates the my_cases master table for the counsel's case portfolio."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS my_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT NOT NULL,
        case_year TEXT NOT NULL,
        case_title TEXT,
        status TEXT NOT NULL DEFAULT 'NEW' CHECK(status IN ('NEW', 'OPEN', 'DISPOSED', 'CLOSED')),
        primary_counsel TEXT,
        associate_counsel TEXT,
        applicant TEXT,
        respondent TEXT,
        requester_department TEXT,
        requester_name TEXT,
        diary_number TEXT,
        date_assigned DATE,
        date_closed DATE,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(case_number, case_year)
    )
    ''')

    conn.commit()
    conn.close()
