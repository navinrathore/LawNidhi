import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from lawnidhi.db.schema import DB_PATH
from lawnidhi.models.my_case_model import MyCaseModel, CaseStatus


def _row_to_model(row: sqlite3.Row) -> MyCaseModel:
    """Convert a sqlite3.Row to a MyCaseModel."""
    d = dict(row)
    return MyCaseModel(**d)


def add_case(case_number: str, case_year: str, **kwargs) -> int:
    """
    Add a new case to the portfolio.
    Returns the new case ID.
    Raises ValueError if case already exists.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns = ['case_number', 'case_year']
    values = [case_number, case_year]

    allowed_fields = [
        'case_title', 'status', 'primary_counsel', 'associate_counsel',
        'applicant', 'respondent', 'requester_department', 'requester_name',
        'diary_number', 'date_assigned', 'date_closed', 'notes'
    ]

    for field in allowed_fields:
        if field in kwargs and kwargs[field] is not None:
            columns.append(field)
            values.append(kwargs[field])

    placeholders = ', '.join(['?'] * len(values))
    col_names = ', '.join(columns)

    try:
        cursor.execute(f'INSERT INTO my_cases ({col_names}) VALUES ({placeholders})', values)
        conn.commit()
        case_id = cursor.lastrowid
        return case_id
    except sqlite3.IntegrityError:
        raise ValueError(f"Case {case_number}/{case_year} already exists in portfolio.")
    finally:
        conn.close()


def update_case(case_number: str, case_year: str, **kwargs) -> bool:
    """
    Update fields of an existing case. Only non-None kwargs are applied.
    Returns True if a row was updated.
    """
    allowed_fields = [
        'case_title', 'status', 'primary_counsel', 'associate_counsel',
        'applicant', 'respondent', 'requester_department', 'requester_name',
        'diary_number', 'date_assigned', 'date_closed', 'notes'
    ]

    updates = {}
    for field in allowed_fields:
        if field in kwargs and kwargs[field] is not None:
            updates[field] = kwargs[field]

    if not updates:
        return False

    updates['updated_at'] = datetime.now().isoformat()

    set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
    values = list(updates.values()) + [case_number, case_year]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'UPDATE my_cases SET {set_clause} WHERE case_number = ? AND case_year = ?',
            values
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_status(case_number: str, case_year: str, status: str) -> bool:
    """Update case status. Auto-sets date_closed when status is CLOSED or DISPOSED."""
    kwargs = {'status': status}
    if status in ('CLOSED', 'DISPOSED'):
        kwargs['date_closed'] = datetime.now().date().isoformat()
    return update_case(case_number, case_year, **kwargs)


def update_diary_number(case_number: str, case_year: str, diary_number: str) -> bool:
    """Set diary number for a case."""
    return update_case(case_number, case_year, diary_number=diary_number)


def get_case(case_number: str, case_year: str) -> Optional[MyCaseModel]:
    """Lookup a single case by case_number and case_year."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT * FROM my_cases WHERE case_number = ? AND case_year = ?',
            (case_number, case_year)
        )
        row = cursor.fetchone()
        return _row_to_model(row) if row else None
    finally:
        conn.close()


def list_cases(status: Optional[str] = None, counsel: Optional[str] = None) -> List[MyCaseModel]:
    """
    List cases with optional filters.
    - status: filter by case status
    - counsel: filter by primary or associate counsel (partial match)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = 'SELECT * FROM my_cases WHERE 1=1'
    params = []

    if status:
        query += ' AND status = ?'
        params.append(status.upper())

    if counsel:
        query += ' AND (primary_counsel LIKE ? OR associate_counsel LIKE ?)'
        pattern = f'%{counsel}%'
        params.append(pattern)
        params.append(pattern)

    query += ' ORDER BY created_at DESC'

    try:
        cursor.execute(query, params)
        return [_row_to_model(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def delete_case(case_number: str, case_year: str) -> bool:
    """Remove a case from the portfolio."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            'DELETE FROM my_cases WHERE case_number = ? AND case_year = ?',
            (case_number, case_year)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
