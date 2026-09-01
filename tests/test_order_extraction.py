"""test_order_extraction.py: Unit tests for Phase 2 Order Triplet Extraction and Precedent Graph Linkage."""
import os
import pytest
from lawnidhi.parsers.ngt.statute_parser import StatuteParser
from lawnidhi.parsers.ngt.order_parser import NGTOrderParser
from lawnidhi.graph.order_sync import ingest_order_extraction
from lawnidhi.graph.store import LegalGraphStore
from lawnidhi.graph.schema import (
    OrderExtractionResult,
    StatuteReference,
    PrecedentCitation,
    JudicialDirection,
)


def test_statute_parser_explicit_patterns():
    text = """
    The applicant approached this Tribunal under Section 14 and Section 15 of the National Green Tribunal Act, 2010.
    It is contended that the industry is operating in violation of Section 25 of the Water (Prevention and Control of Pollution) Act, 1974
    and without obtaining consent to operate under Section 21 of the Air (Prevention and Control of Pollution) Act, 1981.
    Further, directions under Section 33A of Water Act, 1974 were issued.
    The Tribunal also considered Rule 4 of the Solid Waste Management Rules, 2016 and Article 21 of the Constitution of India.
    """
    statutes = StatuteParser.extract_statutes(text)
    assert len(statutes) >= 6

    acts_sections = [(s.act_name, s.section) for s in statutes]
    assert ("National Green Tribunal Act, 2010", "14") in acts_sections
    assert ("National Green Tribunal Act, 2010", "15") in acts_sections
    assert ("Water (Prevention and Control of Pollution) Act, 1974", "25") in acts_sections
    assert ("Water (Prevention and Control of Pollution) Act, 1974", "33A") in acts_sections
    assert ("Air (Prevention and Control of Pollution) Act, 1981", "21") in acts_sections
    assert ("Solid Waste Management Rules, 2016", "4") in acts_sections
    assert ("Constitution of India", "21") in acts_sections


def test_order_parser_precedent_extraction():
    text = """
    In the landmark case of Vellore Citizens Welfare Forum v. Union of India (1996) 5 SCC 647, the Hon'ble Supreme Court
    held that the precautionary principle and polluter pays principle are part of environmental law.
    Reference was also made to M.C. Mehta v. Kamal Nath (1997) 1 SCC 388 regarding the public trust doctrine.
    """
    parser = NGTOrderParser()
    precedents = parser.extract_precedents(text)
    assert len(precedents) >= 2

    titles = [p.case_title for p in precedents]
    assert any("Vellore Citizens" in t for t in titles)
    assert any("Kamal Nath" in t for t in titles)


def test_order_parser_header_parsing():
    sample_header = """
    Item No. 05 Court No. 1
    BEFORE THE NATIONAL GREEN TRIBUNAL
    PRINCIPAL BENCH, NEW DELHI
    Original Application No. 83/2025
    (I.A. No. 132/2025)
    Shakuntla Devi Applicant
    Versus
    Ms. Kiran & Ors. Respondent(s)
    Date of hearing: 28.02.2025
    CORAM: HON’BLE MR. JUSTICE PRAKASH SHRIVASTAVA, CHAIRPERSON
    HON’BLE DR. A. SENTHIL VEL, EXPERT MEMBER
    ORDER
    """
    parser = NGTOrderParser()
    header = parser.parse_header(sample_header)
    assert "83/2025" in header["case_name"]
    assert header["order_date"] == "2025-02-28"
    assert header["court_number"] == "Court 1"
    assert len(header["coram_judges"]) == 2
    assert "PRAKASH SHRIVASTAVA" in header["coram_judges"][0]


def test_ingest_order_extraction_to_graph(tmp_path):
    db_path = str(tmp_path / "kuzu_order_test_db")
    store = LegalGraphStore(db_path=db_path)

    extraction = OrderExtractionResult(
        case_id="case_oa_985_2019",
        case_name="Original Application No. 985/2019",
        order_date="2025-07-01",
        court_number="Court 1",
        bench_judges=["Justice Prakash Shrivastava", "Dr. A. Senthil Vel"],
        invoked_statutes=[
            StatuteReference(act_name="Water (Prevention and Control of Pollution) Act, 1974", section="25")
        ],
        cited_precedents=[
            PrecedentCitation(case_title="Vellore Citizens Welfare Forum v. UOI", citation="5 SCC 647", court="Supreme Court of India", year=1996)
        ],
        directions=[
            JudicialDirection(direction_text="Deposit environmental compensation of Rs. 10 Lakhs", direction_type="PENALTY")
        ]
    )

    stats = ingest_order_extraction(store, extraction)
    assert stats["nodes_added"] >= 5
    assert stats["relations_added"] >= 4

    # Traverse graph
    precedents = store.find_connected_precedents("985/2019")
    assert len(precedents) >= 2
    rel_types = [p["relation"] for p in precedents]
    assert "INVOKES_STATUTE" in rel_types
    assert "CITES_PRECEDENT" in rel_types

    store.close()
