"""test_cause_list_graph.py: Unit tests for Cause List Temporal Knowledge Graph."""
from datetime import date
import pytest
from lawnidhi.models.core import ScheduleModel, CaseModel, CounselModel, PartyModel
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.cause_list import ingest_schedule_to_graph
from lawnidhi.graph.schema import normalize_entity_id, normalize_hearing_id


@pytest.fixture
def graph_store(tmp_path):
    """Fixture providing a temporary LegalGraphStore instance."""
    db_path = str(tmp_path / "kuzu_test_cl_db")
    store = LegalGraphStore(db_path=db_path)
    yield store
    store.close()


def test_ingest_single_schedule(graph_store):
    """Verify ingesting a 1-day cause list schedule creates all expected entities and relations."""
    schedule = ScheduleModel(
        date=date(2025, 3, 14),
        court_no="Court 1",
        judge_name="Hon'ble Justice Prakash Shrivastava",
        list_type="Final",
        cases=[
            CaseModel(
                case_number="83",
                case_year="2025",
                diary_number="1001",
                applicants=[PartyModel(name="Resident Welfare Association", role="Applicant")],
                respondents=[PartyModel(name="Delhi Pollution Control Committee", role="Respondent")],
                counsels=[CounselModel(name="Adv. Sanjay Upadhyay")],
            ),
            CaseModel(
                case_number="84",
                case_year="2025",
                diary_number="1002",
                applicants=[PartyModel(name="Gram Panchayat", role="Applicant")],
                respondents=[PartyModel(name="State of UP", role="Respondent")],
                counsels=[CounselModel(name="Adv. Sanjay Upadhyay")],
            ),
        ]
    )

    res = ingest_schedule_to_graph(schedule, graph_store)
    assert res["cases_ingested"] == 2
    assert res["counsels_ingested"] == 2

    # Check Hearing Entity
    hearing_id = normalize_hearing_id("2025-03-14", "Court 1", "Final")
    hearing = graph_store.get_entity(hearing_id)
    assert hearing is not None
    assert hearing["entity_type"] == "HEARING"
    assert hearing["properties"]["date"] == "2025-03-14"
    assert hearing["properties"]["court_no"] == "Court 1"

    # Check Judge Entity & Relation
    judge_id = normalize_entity_id("JUDGE", "Hon'ble Justice Prakash Shrivastava")
    judge = graph_store.get_entity(judge_id)
    assert judge is not None

    # Check Case Entity
    case1_id = normalize_entity_id("CASE", "OA 83/2025")
    case1 = graph_store.get_entity(case1_id)
    assert case1 is not None

    # Check Neighbors of Case 1
    case1_neighbors = graph_store.get_neighbors(case1_id)
    neighbor_ids = {n["neighbor_id"] for n in case1_neighbors}
    assert hearing_id in neighbor_ids


def test_temporal_hearing_chain_and_history(graph_store):
    """Verify multi-date cause list ingestion builds the temporal FOLLOWS_HEARING chain and listing history."""
    # 1. First hearing on Jan 10, 2025
    schedule1 = ScheduleModel(
        date=date(2025, 1, 10),
        court_no="Court 1",
        judge_name="Hon'ble Justice A. Kumar",
        list_type="Final",
        cases=[
            CaseModel(
                case_number="83",
                case_year="2025",
                counsels=[CounselModel(name="Adv. Sanjay Upadhyay")],
            )
        ]
    )
    ingest_schedule_to_graph(schedule1, graph_store)

    # 2. Second hearing on March 14, 2025 (63 days later)
    schedule2 = ScheduleModel(
        date=date(2025, 3, 14),
        court_no="Court 1",
        judge_name="Hon'ble Justice Prakash Shrivastava",
        list_type="Final",
        cases=[
            CaseModel(
                case_number="83",
                case_year="2025",
                counsels=[CounselModel(name="Adv. Sanjay Upadhyay")],
            )
        ]
    )
    ingest_schedule_to_graph(schedule2, graph_store)

    # Query listing history
    case_id = normalize_entity_id("CASE", "OA 83/2025")
    history = graph_store.get_case_listing_history(case_id)
    assert len(history) == 2

    # Check ascending chronological order
    assert history[0]["date"] == "2025-01-10"
    assert history[0]["days_since_previous"] is None
    assert history[0]["judge_name"] == "Hon'ble Justice A. Kumar"

    assert history[1]["date"] == "2025-03-14"
    assert history[1]["days_since_previous"] == 63
    assert history[1]["judge_name"] == "Hon'ble Justice Prakash Shrivastava"


def test_last_and_next_listing(graph_store):
    """Verify last and next listing calculations relative to a reference date."""
    # Past hearing: 2025-01-10
    ingest_schedule_to_graph(
        ScheduleModel(
            date=date(2025, 1, 10),
            court_no="Court 1",
            judge_name="Justice A",
            cases=[CaseModel(case_number="83", case_year="2025")]
        ),
        graph_store
    )
    # Future hearing: 2025-04-20
    ingest_schedule_to_graph(
        ScheduleModel(
            date=date(2025, 4, 20),
            court_no="Court 1",
            judge_name="Justice B",
            cases=[CaseModel(case_number="83", case_year="2025")]
        ),
        graph_store
    )

    # Query with reference date: 2025-02-15 (in between)
    res = graph_store.get_last_and_next_listing("83/2025", ref_date="2025-02-15")
    assert res["total_hearings"] == 2
    assert res["previous_listing"]["date"] == "2025-01-10"
    assert res["next_listing"]["date"] == "2025-04-20"
    assert res["days_since_last_hearing"] == 36  # 2025-02-15 - 2025-01-10


def test_daily_board_ordering(graph_store):
    """Verify daily courtroom board query orders cases by item number."""
    schedule = ScheduleModel(
        date=date(2025, 3, 14),
        court_no="Court 1",
        judge_name="Justice Prakash Shrivastava",
        cases=[
            CaseModel(case_number="100", case_year="2025"),  # item 1
            CaseModel(case_number="101", case_year="2025"),  # item 2
            CaseModel(case_number="102", case_year="2025"),  # item 3
        ]
    )
    ingest_schedule_to_graph(schedule, graph_store)

    board = graph_store.get_cases_listed_on_date("2025-03-14", court_no="Court 1")
    assert len(board) == 3
    assert board[0]["item_number"] == 1
    assert "100/2025" in board[0]["case_name"]
    assert board[1]["item_number"] == 2
    assert "101/2025" in board[1]["case_name"]
    assert board[2]["item_number"] == 3
    assert "102/2025" in board[2]["case_name"]


def test_counsel_courtroom_clash_detection(graph_store):
    """Verify detection of multi-courtroom appearance clashes for a counsel on the same date."""
    # Court 1 listing for Adv. Sanjay Upadhyay
    schedule_court1 = ScheduleModel(
        date=date(2025, 3, 14),
        court_no="Court 1",
        judge_name="Justice A",
        cases=[
            CaseModel(
                case_number="83",
                case_year="2025",
                counsels=[CounselModel(name="Adv. Sanjay Upadhyay")]
            )
        ]
    )
    # Court 2 listing for Adv. Sanjay Upadhyay on the same morning
    schedule_court2 = ScheduleModel(
        date=date(2025, 3, 14),
        court_no="Court 2",
        judge_name="Justice B",
        cases=[
            CaseModel(
                case_number="200",
                case_year="2025",
                counsels=[CounselModel(name="Adv. Sanjay Upadhyay")]
            )
        ]
    )

    ingest_schedule_to_graph(schedule_court1, graph_store)
    ingest_schedule_to_graph(schedule_court2, graph_store)

    clashes = graph_store.find_counsel_clashes("2025-03-14", "Adv. Sanjay Upadhyay")
    assert len(clashes) == 2
    courtrooms = {c["court_no"] for c in clashes}
    assert "Court 1" in courtrooms
    assert "Court 2" in courtrooms
