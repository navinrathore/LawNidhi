import sqlite3
from typing import Optional, List, Dict
from datetime import date
from lawnidhi.db.schema import DB_PATH

def add_cause_list_record(
    list_date: date,
    list_type: str,
    court_no: str,
    file_path: str,
    source_url: str
) -> int:
    """Add a record of a downloaded cause list. Updates if already exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO cause_lists (date, list_type, court_no, file_path, source_url)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date, list_type, court_no) DO UPDATE SET
                file_path=excluded.file_path,
                source_url=excluded.source_url,
                downloaded_at=CURRENT_TIMESTAMP
        ''', (list_date.isoformat(), list_type, court_no, file_path, source_url))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_cause_list_record(list_date: date, list_type: str, court_no: str) -> Optional[Dict]:
    """Retrieve metadata for a specific cause list."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM cause_lists 
            WHERE date = ? AND list_type = ? AND court_no = ?
        ''', (list_date.isoformat(), list_type, court_no))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def list_downloaded_cause_lists(limit: int = 50) -> List[Dict]:
    """List recent cause list downloads."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM cause_lists ORDER BY date DESC, downloaded_at DESC LIMIT ?', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
