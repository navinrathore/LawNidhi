import os
import sqlite3
import pytest
from lawnidhi.db.schema import create_tables, DB_PATH
from lawnidhi.models.core import CaseModel

@pytest.fixture(scope="module")
def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    create_tables()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_tables_created(setup_database):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'cases' in tables
    assert 'parties' in tables
    assert 'counsels' in tables
    assert 'schedule_cases' in tables
    conn.close()

def test_pydantic_case_model():
    case = CaseModel(case_number="123", case_year="2023", diary_number="D123")
    assert case.case_number == "123"
    assert len(case.applicants) == 0
