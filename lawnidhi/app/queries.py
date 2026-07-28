import sqlite3
from typing import List, Dict
from lawnidhi.db.schema import DB_PATH

def get_cases_by_counsel(counsel_name: str, exact_match: bool = False) -> List[Dict]:
    """Retrieve all scheduled cases for a given counsel name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if exact_match:
        query = "SELECT id FROM counsels WHERE name COLLATE NOCASE = ?"
        cursor.execute(query, (counsel_name,))
    else:
        query = "SELECT id FROM counsels WHERE name LIKE ?"
        cursor.execute(query, (f"%{counsel_name}%",))
        
    counsels = cursor.fetchall()
    if not counsels:
        return []
        
    counsel_ids = [c['id'] for c in counsels]
    placeholders = ','.join('?' for _ in counsel_ids)
    
    sql = f"""
        SELECT c.case_number, c.case_year, c.diary_number, s.schedule_date, s.court_no, s.judge_name
        FROM cases c
        JOIN case_counsels cc ON c.id = cc.case_id
        JOIN schedule_cases sc ON c.id = sc.case_id
        JOIN schedules s ON sc.schedule_id = s.id
        WHERE cc.counsel_id IN ({placeholders})
        ORDER BY s.schedule_date DESC
    """
    cursor.execute(sql, counsel_ids)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_cases_by_counsel_names(names: List[str]) -> List[Dict]:
    """Retrieve all scheduled cases matching ANY of the given counsel names (partial match)."""
    if not names:
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build OR conditions for each name variant
    conditions = ' OR '.join(['name LIKE ?' for _ in names])
    params = [f'%{n}%' for n in names]
    cursor.execute(f'SELECT id FROM counsels WHERE {conditions}', params)

    counsels = cursor.fetchall()
    if not counsels:
        conn.close()
        return []

    counsel_ids = [c['id'] for c in counsels]
    placeholders = ','.join('?' for _ in counsel_ids)

    sql = f"""
        SELECT c.case_number, c.case_year, c.diary_number, s.schedule_date, s.court_no, s.judge_name
        FROM cases c
        JOIN case_counsels cc ON c.id = cc.case_id
        JOIN schedule_cases sc ON c.id = sc.case_id
        JOIN schedules s ON sc.schedule_id = s.id
        WHERE cc.counsel_id IN ({placeholders})
        ORDER BY s.schedule_date DESC
    """
    cursor.execute(sql, counsel_ids)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_case_details(case_number: str, case_year: str = None) -> List[Dict]:
    """Retrieve schedule tracking details for a specific case number."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = """
        SELECT c.case_number, c.case_year, s.schedule_date, s.court_no, s.judge_name
        FROM cases c
        JOIN schedule_cases sc ON c.id = sc.case_id
        JOIN schedules s ON sc.schedule_id = s.id
        WHERE c.case_number = ?
    """
    params = [case_number]
    if case_year:
        sql += " AND c.case_year = ?"
        params.append(case_year)
        
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def list_all_counsels() -> List[str]:
    """List all unique counsel names in the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM counsels ORDER BY name')
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names

def list_all_cases(counsel_name: str = None) -> List[Dict]:
    """List all cases in the DB, optionally filtered by counsel (partial match)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if counsel_name:
        sql = """
            SELECT DISTINCT c.case_number, c.case_year, c.diary_number
            FROM cases c
            JOIN case_counsels cc ON c.id = cc.case_id
            JOIN counsels co ON cc.counsel_id = co.id
            WHERE co.name LIKE ?
            ORDER BY c.case_year DESC, c.case_number
        """
        cursor.execute(sql, (f'%{counsel_name}%',))
    else:
        cursor.execute('SELECT case_number, case_year, diary_number FROM cases ORDER BY case_year DESC, case_number')

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_schedules() -> List[Dict]:
    """List all schedules in the DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.schedule_date, s.court_no, s.judge_name, s.list_type,
               COUNT(sc.case_id) as case_count
        FROM schedules s
        LEFT JOIN schedule_cases sc ON s.id = sc.schedule_id
        GROUP BY s.id
        ORDER BY s.schedule_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_db_stats() -> Dict:
    """Get summary counts of all tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    stats = {}
    for table in ['cases', 'counsels', 'parties', 'schedules', 'my_cases']:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = cursor.fetchone()[0]
        except Exception:
            stats[table] = 0
    conn.close()
    return stats

if __name__ == "__main__":
    import pprint
    print("Cases for 'Hemlata Singh':")
    pprint.pprint(get_cases_by_counsel("Hemlata Singh"))
