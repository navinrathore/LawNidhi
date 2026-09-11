#!/usr/bin/env python3
import argparse
import sys
from lawnidhi.db.schema import create_tables
from lawnidhi.parsers.ngt.cause_list_parser import NGTCauseListParser
from lawnidhi.db.ingest import ingest_schedule
from lawnidhi.app.reports import generate_counsel_appearance_log
from lawnidhi.scraper.ngt_order_scraper import NGTOrderScraper
from lawnidhi.scraper.dynamic_search import DynamicSearchAPI
from lawnidhi.scraper.ngt_cause_list_scraper import NGTCauseListScraper
from lawnidhi.db import my_cases_repo, cause_list_repo
from lawnidhi import config
from lawnidhi.app import queries

def parse_case_input(case_input: str) -> tuple:
    """Parse case input in '83/2025' or '83 2025' format into (case_no, case_year)."""
    if '/' in case_input:
        parts = case_input.split('/', 1)
        return parts[0].strip(), parts[1].strip()
    raise argparse.ArgumentTypeError(f"Invalid case format '{case_input}'. Use format: 83/2025")

def _resolve_case_args(args):
    """Resolve case_no and case_year from either '83/2025' or '83' '2025' format."""
    if '/' in args.case:
        case_no, case_year = parse_case_input(args.case)
    else:
        case_no = args.case
        case_year = args.case_year
    if not case_year:
        print("Error: Case year is required. Use format '83/2025' or provide case_year separately.")
        sys.exit(1)
    return case_no, case_year

def main():
    parser = argparse.ArgumentParser(
        description="LawNidhi: NGT Order Scraper & Case Portfolio Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
\033[92mUsage Groups:\033[0m
  \033[93m[CORE PIPELINE]\033[0m
    \033[96msync-cause-lists\033[0m        - Scan NGT site and update DB with new schedules
    \033[96msearch-case\033[0m             - Lookup case details and diary numbers
    \033[96mdownload-case-orders\033[0m    - Full pipeline to fetch and save PDFs

  \033[93m[MY PORTFOLIO]\033[0m
    \033[96madd-case / update-case\033[0m  - Manage your assigned cases
    \033[96mlist-cases / show-case\033[0m  - Browse your portfolio
    \033[96mclose-case\033[0m              - Mark a case as DISPOSED/CLOSED

  \033[93m[REPORTS]\033[0m
    \033[96mgenerate-invoice\033[0m        - Create appearance logs for billing

  \033[93m[KNOWLEDGE GRAPH]\033[0m
    \033[96mgraph-stats\033[0m             - View Knowledge Graph node & relationship counts
    \033[96mgraph-sync\033[0m              - Sync all cause list PDFs into Knowledge Graph
    \033[96mgraph-timeline\033[0m          - View chronological hearing timeline for a case
    \033[96mgraph-daily-board\033[0m       - View daily courtroom cause list board (today/tomorrow)
    \033[96mgraph-counsel-cases\033[0m     - View listed cases for a specific counsel (today/tomorrow)
    \033[96mgraph-counsel-clashes\033[0m   - Detect multi-courtroom appearance clashes

  \033[93m[EXPLORATION]\033[0m
    \033[96mlist-db-cases\033[0m           - Search all historical cause-list data
    \033[96mlist-counsels\033[0m           - Browse unique names in the DB
    \033[96mlist-schedules\033[0m          - View all parsed hearing dates
    \033[96mdb-stats\033[0m                - Database health and row counts

  \033[93m[SYSTEM]\033[0m
    \033[96minit-db\033[0m                 - Initialize/Update DB schema
    \033[96mparse-cause-list\033[0m        - Manually parse a local NGT PDF
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- KNOWLEDGE GRAPH ---
    subparsers.add_parser("graph-stats", help="View Knowledge Graph statistics and entity breakdown")
    
    gsync_parser = subparsers.add_parser("graph-sync", help="Ingest all downloaded cause lists into the Knowledge Graph")
    gsync_parser.add_argument("--dir", default=None, help="Custom directory containing cause list PDFs")

    gtl_parser = subparsers.add_parser("graph-timeline", help="View chronological listing timeline for a case")
    gtl_parser.add_argument("case", help="Case number (e.g. 606/2018 or 83/2025)")

    gdb_parser = subparsers.add_parser("graph-daily-board", help="View cause list board for a specific date")
    gdb_parser.add_argument("date", nargs="?", default="today", help="Hearing date (YYYY-MM-DD, 'today', or 'tomorrow')")
    gdb_parser.add_argument("--court", default=None, help="Optional court number filter (e.g. 'Court 1')")

    gcs_parser = subparsers.add_parser("graph-counsel-cases", help="View listed cases for a specific counsel across dates")
    gcs_parser.add_argument("counsel", help="Counsel name (e.g. 'Bhanwar Pal Singh')")
    gcs_parser.add_argument("--start", default="today", help="Start date (default: today)")
    gcs_parser.add_argument("--end", default=None, help="End date (default: tomorrow if days=2)")
    gcs_parser.add_argument("--days", type=int, default=2, help="Number of days to display (default: 2 for today and tomorrow)")

    gcc_parser = subparsers.add_parser("graph-counsel-clashes", help="Detect courtroom scheduling clashes for a counsel")
    gcc_parser.add_argument("date", nargs="?", default="today", help="Hearing date (YYYY-MM-DD, 'today', or 'tomorrow')")
    gcc_parser.add_argument("counsel", default=None, nargs="?", help="Counsel name (default: from config)")

    gpr_parser = subparsers.add_parser("graph-precedents", help="Discover citations, precedents, and statutes for a case")
    gpr_parser.add_argument("case", help="Case number (e.g. 630/2023 or 606/2018)")

    gcp_parser = subparsers.add_parser("graph-counsel-portfolio", help="View lifetime representation portfolio for a counsel")
    gcp_parser.add_argument("counsel", help="Counsel name (e.g. 'Bhanwar Pal Singh')")

    gjb_parser = subparsers.add_parser("graph-judge-bench", help="View judge caseload, hearings presided, and cases heard")
    gjb_parser.add_argument("judge", help="Judge name (e.g. 'Prakash Shrivastava')")

    gq_parser = subparsers.add_parser("graph-query", help="Execute a raw openCypher query on the Knowledge Graph")
    gq_parser.add_argument("query", help="openCypher query string (e.g. 'MATCH (n:LegalEntity) RETURN n.entity_type, count(n)')")

    gexp_parser = subparsers.add_parser("graph-export", help="Export Knowledge Graph topology in JSON, DOT, or GEXF")
    gexp_parser.add_argument("--format", choices=["json", "dot", "gexf"], default="json", help="Export format (default: json)")
    gexp_parser.add_argument("--out", default=None, help="Optional output file path to write to")

    geo_parser = subparsers.add_parser("graph-extract-order", help="Extract statutes, precedents, and coram from an NGT Order PDF")
    geo_parser.add_argument("pdf_path", help="Path to the order PDF file")
    geo_parser.add_argument("--ingest", action="store_true", help="Automatically merge extracted triplets into Knowledge Graph")

    gso_parser = subparsers.add_parser("graph-sync-orders", help="Batch extract and ingest all order PDFs into Knowledge Graph")
    gso_parser.add_argument("--dir", default=None, help="Directory containing order PDFs (default: data/orders/)")

    # serve
    srv_parser = subparsers.add_parser("serve", help="Start the FastAPI Knowledge Graph REST API server")
    srv_parser.add_argument("--host", default="127.0.0.1", help="Host address to bind to (default: 127.0.0.1)")
    srv_parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    srv_parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    # graph-rag
    grag_parser = subparsers.add_parser("graph-rag", help="Hybrid GraphRAG retriever: vector search + multi-hop graph expansion")
    grag_parser.add_argument("query", help="Legal research query (e.g. 'Water Act Section 25 penalties')")
    grag_parser.add_argument("--top-k", type=int, default=3, help="Number of text chunks to retrieve (default: 3)")
    grag_parser.add_argument("--synthesize", action="store_true", help="Generate a synthesized grounded legal answer")

    # graph-communities
    gc_parser = subparsers.add_parser("graph-communities", help="Detect and display macro-thematic graph communities")
    gc_parser.add_argument("--min-size", type=int, default=2, help="Minimum node size to include a community (default: 2)")

    # ask (Agentic Co-Counsel)
    ask_parser = subparsers.add_parser("ask", help="Autonomous Agentic Legal Co-Counsel: multi-step reasoning, graph querying, and brief drafting")
    ask_parser.add_argument("query", help="Complex legal research query or case brief instruction")
    ask_parser.add_argument("--max-loops", type=int, default=10, help="Maximum ReAct loop iterations (default: 10)")
    ask_parser.add_argument("--verbose", action="store_true", help="Print intermediate ReAct thoughts and tool observations")

    # init-db is moved to the SYSTEM group below

    # parse-pdf
    parse_parser = subparsers.add_parser("parse-pdf", help="Parse an NGT Cause List PDF and ingest to DB")
    # --- CORE PIPELINE ---
    
    # sync-cause-lists
    sys_parser = subparsers.add_parser("sync-cause-lists", help="Automated: scan chairperson bench -> download -> parse -> ingest")
    sys_parser.add_argument("--start", help="Start date (YYYY-MM-DD, default: today)")

    # search-case
    sc_parser = subparsers.add_parser("search-case", help="Search for a case by number and year to find Diary Number")
    sc_parser.add_argument("case", help="Case in '83/2025' format, or just the case number")
    sc_parser.add_argument("case_year", nargs="?", default=None, help="Case year (if not using 83/2025 format)")
    sc_parser.add_argument("--zone", default=config.get_default_zone(), help="Zone type (default: from config)")
    sc_parser.add_argument("--case-type", default=config.get_default_case_type(), help="Case type (default: from config)")

    # download-case-orders
    dco_parser = subparsers.add_parser("download-case-orders", help="Full pipeline: search case -> solve CAPTCHA -> download order PDFs")
    dco_parser.add_argument("case", help="Case in '83/2025' format, or just the case number")
    dco_parser.add_argument("case_year", nargs="?", default=None, help="Case year (if not using 83/2025 format)")
    dco_parser.add_argument("--dir", default=config.get_default_download_dir(), help="Directory to save PDFs to")
    dco_parser.add_argument("--zone", default=config.get_default_zone(), help="Zone type (default: from config)")
    dco_parser.add_argument("--case-type", default=config.get_default_case_type(), help="Case type (default: from config)")
    dco_parser.add_argument("--retries", type=int, default=3, help="Max CAPTCHA retry attempts (default: 3)")
    dco_parser.add_argument("--all", action="store_true", dest="download_all", help="Download all orders without prompting")
    dco_parser.add_argument("--order", type=int, nargs="+", dest="order_indices", help="Download specific orders by number (e.g., --order 1 3)")

    # --- MY PORTFOLIO ---

    # add-case
    ac_parser = subparsers.add_parser("add-case", help="Add a case to your portfolio")
    ac_parser.add_argument("case", help="Case in '83/2025' format")
    ac_parser.add_argument("--title", help="Short case description")
    ac_parser.add_argument("--counsel", default=config.get_counsel_name(), help="Primary counsel name (default: from config)")
    ac_parser.add_argument("--associate", help="Associate counsel name(s)")
    ac_parser.add_argument("--applicant", help="Applicant/client name")
    ac_parser.add_argument("--respondent", help="Respondent/opposition name")
    ac_parser.add_argument("--status", default="NEW", choices=["NEW", "OPEN", "DISPOSED", "CLOSED"], help="Case status (default: NEW)")
    ac_parser.add_argument("--department", help="Requester department")
    ac_parser.add_argument("--requester", help="Requester name")
    ac_parser.add_argument("--diary", help="Diary number (if known)")
    ac_parser.add_argument("--notes", help="Additional notes")

    # update-case
    uc_parser = subparsers.add_parser("update-case", help="Update fields of an existing case")
    uc_parser.add_argument("case", help="Case in '83/2025' format")
    uc_parser.add_argument("--title", help="Short case description")
    uc_parser.add_argument("--counsel", help="Primary counsel name")
    uc_parser.add_argument("--associate", help="Associate counsel name(s)")
    uc_parser.add_argument("--applicant", help="Applicant/client name")
    uc_parser.add_argument("--respondent", help="Respondent/opposition name")
    uc_parser.add_argument("--status", choices=["NEW", "OPEN", "DISPOSED", "CLOSED"], help="Case status")
    uc_parser.add_argument("--department", help="Requester department")
    uc_parser.add_argument("--requester", help="Requester name")
    uc_parser.add_argument("--diary", help="Diary number")
    uc_parser.add_argument("--notes", help="Additional notes")

    # list-cases
    lc_parser = subparsers.add_parser("list-cases", help="List cases in your portfolio")
    lc_parser.add_argument("--status", choices=["NEW", "OPEN", "DISPOSED", "CLOSED"], help="Filter by status")
    lc_parser.add_argument("--counsel", help="Filter by counsel name (partial match)")

    # show-case
    shc_parser = subparsers.add_parser("show-case", help="Show full details of a case")
    shc_parser.add_argument("case", help="Case in '83/2025' format")

    # close-case
    cc_parser = subparsers.add_parser("close-case", help="Set a case status to CLOSED")
    cc_parser.add_argument("case", help="Case in '83/2025' format")

    # --- REPORTS ---

    # generate-invoice
    inv_parser = subparsers.add_parser("generate-invoice", help="Generate an appearance log for a counsel")
    inv_parser.add_argument("counsel", nargs="?", default=config.get_counsel_name(), help="Counsel name (default: from config)")
    inv_parser.add_argument("--start", help="Start date (YYYY-MM-DD)", default=None)
    inv_parser.add_argument("--end", help="End date (YYYY-MM-DD)", default=None)

    # --- EXPLORATION ---

    # list-db-cases
    ldc_parser = subparsers.add_parser("list-db-cases", help="List all cases from parsed cause lists")
    ldc_parser.add_argument("--counsel", help="Filter by counsel name (partial match)")
    
    # list-counsels
    lco_parser = subparsers.add_parser("list-counsels", help="List all unique counsel names in the DB")
    lco_parser.add_argument("--search", help="Filter counsel names (partial match)")

    # list-schedules
    subparsers.add_parser("list-schedules", help="List all parsed schedules")

    # db-stats
    subparsers.add_parser("db-stats", help="Show summary counts of all DB tables")

    # --- SYSTEM ---

    # init-db
    subparsers.add_parser("init-db", help="Initialize/Update the database schema")
    
    # parse-cause-list (manual)
    pcl_parser = subparsers.add_parser("parse-cause-list", help="Parse a local NGT cause list PDF")
    pcl_parser.add_argument("pdf_path", help="Path to the PDF file")

    args = parser.parse_args()

    if args.command == "init-db":
        create_tables()
        print("Database schema successfully initialized.")
        
    elif args.command == "parse-pdf":
        print(f"Parsing {args.filepath}...")
        p = NGTCauseListParser()
        try:
            schedule = p.parse(args.filepath)
            print(f"Parsed {len(schedule.cases)} cases for Date: {schedule.date}.")
            sched_id = ingest_schedule(schedule)
            print(f"Successfully ingested into Database. Schedule ID: {sched_id}")
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            
    elif args.command == "download-order":
        scraper = NGTOrderScraper(args.dir)
        scraper.download_pdf(args.url, args.filename)

    elif args.command == "search-case":
        case_no, case_year = _resolve_case_args(args)
        api = DynamicSearchAPI()
        result = api.auto_search(case_no, case_year, args.zone, args.case_type, args.retries)
        
        if result["success"]:
            html_result = result["html"]
            details = api.extract_diary_number_and_links(html_result)
            diary = details.get('diary_number', 'N/A')
            print(f"\nDiary Number: {diary}")
            orders = api.list_available_orders(details)
            if orders:
                print(f"Found {len(orders)} Order(s):")
                for i, order in enumerate(orders, 1):
                    print(f"  {i}. [{order['order_date']}] {order['suggested_filename']}")
            else:
                print("No downloadable orders found.")
        else:
            print(f"Search failed: {result.get('message', 'CAPTCHA may have failed after retries.')}")

    elif args.command == "download-case-orders":
        case_no, case_year = _resolve_case_args(args)
        api = DynamicSearchAPI()
        result = api.auto_search(case_no, case_year, args.zone, args.case_type, args.retries)
        
        if result["success"]:
            html_result = result["html"]
            details = api.extract_diary_number_and_links(html_result)
            diary = details.get('diary_number', 'N/A')
            print(f"\nDiary Number: {diary}")
            orders = api.list_available_orders(details)
            if not orders:
                print("No downloadable orders found.")
            else:
                print(f"\nAvailable Orders ({len(orders)}):")
                for i, order in enumerate(orders, 1):
                    print(f"  {i}. [{order['order_date']}] {order['suggested_filename']}")
                
                # Selection logic (Auto or Interactive)
                if args.download_all:
                    indices = None
                elif args.order_indices:
                    indices = args.order_indices
                else:
                    print(f"\nEnter order numbers to download (e.g., '1 3'), 'all', or 'q' to quit:")
                    choice = input("> ").strip().lower()
                    if choice == 'q':
                        print("Aborted.")
                        sys.exit(0)
                    elif choice == 'all':
                        indices = None
                    else:
                        try:
                            indices = [int(x) for x in choice.split()]
                        except ValueError:
                            print(f"Invalid input: '{choice}'")
                            sys.exit(1)

                saved = api.download_selected_orders(orders, indices=indices, download_dir=args.dir)
                print(f"\nDownloaded {len(saved)} order(s):")
                for path in saved:
                    print(f"  -> {path}")
        else:
            print(f"Failed to retrieve case details: {result.get('message', 'CAPTCHA may have failed.')}")

    elif args.command == "generate-invoice":
        report = generate_counsel_appearance_log(args.counsel, args.start, args.end)
        print(report)

    # === Case Portfolio Handlers ===

    elif args.command == "add-case":
        case_no, case_year = _resolve_case_args(args)
        try:
            case_id = my_cases_repo.add_case(
                case_no, case_year,
                case_title=args.title,
                status=args.status,
                primary_counsel=args.counsel,
                associate_counsel=args.associate,
                applicant=args.applicant,
                respondent=args.respondent,
                requester_department=args.department,
                requester_name=args.requester,
                diary_number=args.diary,
                notes=args.notes
            )
            print(f"Case {case_no}/{case_year} added to portfolio. (ID: {case_id})")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "update-case":
        case_no, case_year = _resolve_case_args(args)
        kwargs = {}
        if args.title: kwargs['case_title'] = args.title
        if args.status: kwargs['status'] = args.status
        if args.counsel: kwargs['primary_counsel'] = args.counsel
        if args.associate: kwargs['associate_counsel'] = args.associate
        if args.applicant: kwargs['applicant'] = args.applicant
        if args.respondent: kwargs['respondent'] = args.respondent
        if args.department: kwargs['requester_department'] = args.department
        if args.requester: kwargs['requester_name'] = args.requester
        if args.diary: kwargs['diary_number'] = args.diary
        if args.notes: kwargs['notes'] = args.notes

        if not kwargs:
            print("No fields to update. Use --help to see available options.")
            sys.exit(1)

        if args.status:
            updated = my_cases_repo.update_status(case_no, case_year, args.status)
        else:
            updated = my_cases_repo.update_case(case_no, case_year, **kwargs)

        if updated:
            print(f"Case {case_no}/{case_year} updated.")
        else:
            print(f"Case {case_no}/{case_year} not found in portfolio.")

    elif args.command == "list-cases":
        cases = my_cases_repo.list_cases(status=args.status, counsel=args.counsel)
        if not cases:
            print("No cases found.")
        else:
            print(f"\n{'#':<4} {'Case':<15} {'Status':<10} {'Counsel':<20} {'Title'}")
            print("-" * 70)
            for i, c in enumerate(cases, 1):
                case_id = c.display_case_id()
                counsel = c.primary_counsel or "-"
                title = c.case_title or "-"
                print(f"{i:<4} {case_id:<15} {c.status.value:<10} {counsel:<20} {title}")
            print(f"\nTotal: {len(cases)} case(s)")

    elif args.command == "show-case":
        case_no, case_year = _resolve_case_args(args)
        c = my_cases_repo.get_case(case_no, case_year)
        if not c:
            print(f"Case {case_no}/{case_year} not found in portfolio.")
            sys.exit(1)
        print(f"\n{'='*50}")
        print(f"  CASE DETAILS: {c.display_case_id()}")
        print(f"{'='*50}")
        print(f"  Title      : {c.case_title or '-'}")
        print(f"  Status     : {c.status.value}")
        print(f"  Counsel    : {c.primary_counsel or '-'}")
        print(f"  Associate  : {c.associate_counsel or '-'}")
        print(f"  Applicant  : {c.applicant or '-'}")
        print(f"  Respondent : {c.respondent or '-'}")
        print(f"  Department : {c.requester_department or '-'}")
        print(f"  Requester  : {c.requester_name or '-'}")
        print(f"  Diary No.  : {c.diary_number or '-'}")
        print(f"  Assigned   : {c.date_assigned or '-'}")
        print(f"  Closed     : {c.date_closed or '-'}")
        print(f"  Notes      : {c.notes or '-'}")
        print(f"  Created    : {c.created_at}")
        print(f"  Updated    : {c.updated_at}")
        print(f"{'='*50}")

    elif args.command == "close-case":
        case_no, case_year = _resolve_case_args(args)
        updated = my_cases_repo.update_status(case_no, case_year, "CLOSED")
        if updated:
            print(f"Case {case_no}/{case_year} is now CLOSED.")
        else:
            print(f"Case {case_no}/{case_year} not found in portfolio.")

    elif args.command == "sync-cause-lists":
        from datetime import date
        start = date.today()
        if args.start:
            try:
                from datetime import datetime
                start = datetime.strptime(args.start, "%Y-%m-%d").date()
            except ValueError:
                print("Error: Invalid date format. Use YYYY-MM-DD.")
                sys.exit(1)
        
        scraper = NGTCauseListScraper()
        processed = scraper.sync(start_date=start)
        print(f"Successfully processed {processed} cause lists.")

    # === DB Exploration Handlers ===

    elif args.command == "db-stats":
        stats = queries.get_db_stats()
        print("\nDatabase Statistics:")
        print("-" * 30)
        for table, count in stats.items():
            print(f"  {table:<15} {count:>5} rows")

    elif args.command == "list-counsels":
        names = queries.list_all_counsels()
        if args.search:
            names = [n for n in names if args.search.lower() in n.lower()]
        if not names:
            print("No counsels found.")
        else:
            print(f"\nCounsels ({len(names)}):")
            for i, name in enumerate(names, 1):
                print(f"  {i:>3}. {name}")

    elif args.command == "list-db-cases":
        cases = queries.list_all_cases(counsel_name=args.counsel)
        if not cases:
            print("No cases found.")
        else:
            print(f"\n{'#':<4} {'Case':<20} {'Diary Number'}")
            print("-" * 50)
            for i, c in enumerate(cases, 1):
                case_id = f"{c['case_number']}/{c['case_year']}" if c['case_year'] else c['case_number']
                diary = c.get('diary_number') or '-'
                print(f"{i:<4} {case_id:<20} {diary}")
            print(f"\nTotal: {len(cases)} case(s)")

    elif args.command == "list-schedules":
        schedules = queries.list_schedules()
        if not schedules:
            print("No schedules found.")
        else:
            print(f"\n{'Date':<14} {'Court':<8} {'Type':<14} {'Cases':<6} {'Judge'}")
            print("-" * 70)
            for s in schedules:
                print(f"{s['schedule_date']:<14} {s['court_no'] or '-':<8} {s['list_type']:<14} {s['case_count']:<6} {s['judge_name'] or '-'}")
            print(f"\nTotal: {len(schedules)} schedule(s)")

    # === Knowledge Graph Handlers ===

    elif args.command == "graph-stats":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        stats = store.get_graph_stats()
        print("\n\033[92m🏛️  Knowledge Graph Statistics (Kùzu DB):\033[0m")
        print("-" * 40)
        print(f"  Total Graph Nodes:         {stats['total_nodes']:>6}")
        print(f"  Total Relationships:       {stats['total_relationships']:>6}")
        print("\n  \033[93mEntity Breakdown:\033[0m")
        for ent_type, count in sorted(stats['entity_breakdown'].items()):
            print(f"    • {ent_type:<18} {count:>6} nodes")
        store.close()

    elif args.command == "graph-sync":
        import glob
        import os
        from lawnidhi.parsers.ngt.cause_list_parser import NGTCauseListParser
        from lawnidhi.graph.cause_list import ingest_schedule_to_graph
        from lawnidhi.graph.store import LegalGraphStore

        target_dir = args.dir or os.path.join(os.path.dirname(__file__), "data", "cause_lists")
        pdf_files = sorted(glob.glob(os.path.join(target_dir, "*.pdf")))
        if not pdf_files:
            print(f"No cause list PDFs found in {target_dir}")
            sys.exit(0)

        print(f"\n\033[92m🔄 Syncing {len(pdf_files)} Cause List PDFs into Knowledge Graph...\033[0m")
        parser_inst = NGTCauseListParser()
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)

        total_cases = 0
        total_relations = 0
        for pdf in pdf_files:
            try:
                sched = parser_inst.parse(pdf)
                res = ingest_schedule_to_graph(sched, store)
                print(f"  ✓ {os.path.basename(pdf):<32} -> {res['cases_ingested']:>2} cases, {res['relations_created']:>3} relations")
                total_cases += res['cases_ingested']
                total_relations += res['relations_created']
            except Exception as e:
                print(f"  ✗ Error parsing {os.path.basename(pdf)}: {e}")

        stats = store.get_graph_stats()
        print(f"\n\033[92m✓ Sync Complete!\033[0m Graph now contains {stats['total_nodes']} nodes and {stats['total_relationships']} relationships.")
        store.close()

    elif args.command == "graph-timeline":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        history = store.get_case_listing_history(args.case)
        if not history:
            print(f"No hearing records found in Knowledge Graph for case '{args.case}'.")
        else:
            print(f"\n\033[92m📅 Listing Timeline for Case: {args.case} (Total Hearings: {len(history)})\033[0m")
            print("-" * 80)
            print(f"{'Date':<14} {'Court':<10} {'Item':<6} {'Gap':<16} {'Presiding Judge'}")
            print("-" * 80)
            for h in history:
                gap_str = f"+{h['days_since_previous']} days gap" if h['days_since_previous'] is not None else "First listing"
                item_str = str(h['item_number']) if h['item_number'] is not None else "-"
                judge_str = (h['judge_name'][:30] + '..') if h['judge_name'] and len(h['judge_name']) > 32 else (h['judge_name'] or '-')
                print(f"{h['date']:<14} {h['court_no']:<10} {item_str:<6} {gap_str:<16} {judge_str}")
        store.close()

    elif args.command == "graph-daily-board":
        import os
        from datetime import date, timedelta
        from lawnidhi.graph.store import LegalGraphStore

        date_arg = args.date.lower() if args.date else "today"
        if date_arg == "today":
            target_date = date.today().isoformat()
        elif date_arg == "tomorrow":
            target_date = (date.today() + timedelta(days=1)).isoformat()
        else:
            target_date = args.date

        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        cases = store.get_cases_listed_on_date(target_date, court_no=args.court)
        if not cases:
            print(f"No cases listed on {target_date} in the Knowledge Graph.")
        else:
            court_header = f" ({args.court})" if args.court else ""
            print(f"\n\033[92m📋 Daily Board for {target_date}{court_header} (Total Items: {len(cases)})\033[0m")
            print("-" * 135)
            print(f"{'Item':<6} {'Court':<8} {'Case Title / Number':<36} {'Counsel(s)':<45} {'Judge'}")
            print("-" * 135)
            for c in cases:
                case_title = (c['case_name'][:34] + '..') if len(c['case_name']) > 36 else c['case_name']
                counsels = c.get('counsels', '-')
                judge_title = c.get('judge_name', '-')
                print(f"{c['item_number']:<6} {c['court_no']:<8} {case_title:<36} {counsels:<45} {judge_title}")
        store.close()

    elif args.command == "graph-counsel-cases":
        import os
        from datetime import date, datetime, timedelta
        from lawnidhi.graph.store import LegalGraphStore

        start_arg = args.start.lower() if args.start else "today"
        if start_arg == "today":
            start_date = date.today().isoformat()
        elif start_arg == "tomorrow":
            start_date = (date.today() + timedelta(days=1)).isoformat()
        else:
            start_date = args.start

        if args.end:
            end_arg = args.end.lower()
            if end_arg == "today":
                end_date = date.today().isoformat()
            elif end_arg == "tomorrow":
                end_date = (date.today() + timedelta(days=1)).isoformat()
            else:
                end_date = args.end
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = (start_dt + timedelta(days=max(0, args.days - 1))).isoformat()

        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        appearances = store.get_counsel_schedule(args.counsel, start_date=start_date, end_date=end_date)
        
        if not appearances:
            print(f"No scheduled cases found for counsel '{args.counsel}' between {start_date} and {end_date}.")
        else:
            counsel_name = appearances[0]['counsel_name']
            print(f"\n\033[92m⚖️  Scheduled Cases for '{counsel_name}' ({start_date} to {end_date}) [Total: {len(appearances)}]:\033[0m")
            print("-" * 90)
            print(f"{'Date':<12} {'Court':<8} {'Item':<6} {'Type':<12} {'Case Title / Number':<34} {'Judge'}")
            print("-" * 90)
            for a in appearances:
                case_title = (a['case_name'][:32] + '..') if len(a['case_name']) > 34 else a['case_name']
                judge_title = (a['judge_name'][:18] + '..') if len(a['judge_name']) > 20 else (a['judge_name'] or '-')
                item_str = str(a['item_number']) if a['item_number'] is not None else "-"
                print(f"{a['date']:<12} {a['court_no']:<8} {item_str:<6} {a['list_type']:<12} {case_title:<34} {judge_title}")
        store.close()

    elif args.command == "graph-counsel-clashes":
        import os
        from datetime import date, timedelta
        from lawnidhi.graph.store import LegalGraphStore

        date_arg = args.date.lower() if args.date else "today"
        if date_arg == "today":
            target_date = date.today().isoformat()
        elif date_arg == "tomorrow":
            target_date = (date.today() + timedelta(days=1)).isoformat()
        else:
            target_date = args.date

        counsel_name = args.counsel or config.get_counsel_name()
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        clashes = store.find_counsel_clashes(target_date, counsel_name)
        if not clashes:
            print(f"\n\033[92m✓ No courtroom clashes detected for '{counsel_name}' on {target_date}.\033[0m")
        else:
            print(f"\n\033[91m⚠️  COURTROOM CLASH DETECTED for '{counsel_name}' on {target_date}!\033[0m")
            print("-" * 75)
            for c in clashes:
                print(f"  • {c['court_no']} | Item {c.get('item_number') or '-'}: {c['case_name']} (Judge: {c['judge_name']})")
        store.close()

    elif args.command == "graph-precedents":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        
        precedents = store.find_connected_precedents(args.case)
        if not precedents:
            print(f"\nNo precedent citations or invoked statutes found in graph for case '{args.case}'.")
            print("Tip: Precedents are populated when judgment PDFs are extracted.")
        else:
            print(f"\n\033[92m⚖️  Connected Precedents & Statutes for Case '{args.case}' [Total: {len(precedents)}]:\033[0m")
            print("-" * 85)
            print(f"{'Relation':<20} {'Target Entity':<35} {'Sub-Citation'}")
            print("-" * 85)
            for p in precedents:
                sub_info = f"{p['sub_relation']} -> {p['sub_target_name']}" if p.get('sub_relation') and p.get('sub_target_name') else "-"
                print(f"{p['relation']:<20} {p['target_name']:<35} {sub_info}")
        store.close()

    elif args.command == "graph-counsel-portfolio":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        
        portfolio = store.get_counsel_portfolio(args.counsel)
        if portfolio["total_cases"] == 0:
            print(f"\nNo lifetime representation records found for counsel '{args.counsel}' in Knowledge Graph.")
        else:
            print(f"\n\033[92m👤 Lifetime Counsel Portfolio: {portfolio['counsel_name']} (Total Cases: {portfolio['total_cases']})\033[0m")
            print("=" * 95)
            print(f"{'Case Title / Number':<40} {'Court':<10} {'Last Listing':<15} {'Judge'}")
            print("-" * 95)
            for c in portfolio["cases"]:
                title = (c['case_name'][:38] + '..') if len(c['case_name']) > 40 else c['case_name']
                print(f"{title:<40} {c['court_no']:<10} {c['last_hearing']:<15} {c['judge']}")
            
            if portfolio["distinct_judges"]:
                print("\n\033[96m🏛️  Benches Appeared Before:\033[0m")
                for j in portfolio["distinct_judges"]:
                    print(f"  • {j}")

            if portfolio["distinct_parties"]:
                print(f"\n\033[96m👥 Parties Represented ({len(portfolio['distinct_parties'])} clients/respondents):\033[0m")
                for p in portfolio["distinct_parties"][:10]:
                    print(f"  • {p}")
                if len(portfolio["distinct_parties"]) > 10:
                    print(f"  ... and {len(portfolio['distinct_parties']) - 10} more")
        store.close()

    elif args.command == "graph-judge-bench":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        
        caseload = store.get_judge_caseload(args.judge)
        if caseload["total_hearings"] == 0:
            print(f"\nNo presiding records found for judge '{args.judge}' in Knowledge Graph.")
        else:
            print(f"\n\033[92m🏛️  Bench Caseload: {caseload['judge_name']}\033[0m")
            print(f"Total Hearings Presided: {caseload['total_hearings']} | Total Unique Cases: {caseload['total_cases']}")
            print("=" * 80)
            for h in caseload["hearings"][:10]:
                print(f"\n📅 Hearing: {h['date']} ({h['court_no']} - {h['list_type']} List) [Items: {h['cases_count']}]:")
                for item in h["items"][:5]:
                    print(f"   Item {item['item_number']:<4}: {item['case_name']}")
                if len(h["items"]) > 5:
                    print(f"   ... and {len(h['items']) - 5} more items")
            if len(caseload["hearings"]) > 10:
                print(f"\n... and {len(caseload['hearings']) - 10} more hearing sessions.")
        store.close()

    elif args.command == "graph-query":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        
        try:
            res = store.execute_raw_cypher(args.query)
            print(f"\n\033[92m⚡ Query Result ({res['row_count']} rows):\033[0m")
            print("-" * 80)
            for row in res["rows"]:
                print(" | ".join(str(cell) for cell in row))
        except Exception as e:
            print(f"\033[91mQuery Execution Error: {e}\033[0m")
        store.close()

    elif args.command == "graph-export":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        
        try:
            output = store.export_graph_format(args.format)
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(output)
                print(f"\n\033[92m✓ Successfully exported graph to '{args.out}' in {args.format.upper()} format.\033[0m")
            else:
                print(output)
        except Exception as e:
            print(f"\033[91mExport Error: {e}\033[0m")
        store.close()

    elif args.command == "graph-extract-order":
        import os
        from lawnidhi.parsers.ngt.order_parser import NGTOrderParser
        from lawnidhi.graph.order_sync import ingest_order_extraction
        from lawnidhi.graph.store import LegalGraphStore

        pdf_path = args.pdf_path
        if not os.path.exists(pdf_path):
            print(f"\033[91mError: File not found: '{pdf_path}'\033[0m")
            sys.exit(1)

        print(f"\n\033[96m📄 Parsing Order PDF: {os.path.basename(pdf_path)}...\033[0m")
        parser = NGTOrderParser()
        extraction = parser.parse_order(pdf_path)

        print(f"\n\033[92m⚖️  Order Extraction Results:\033[0m")
        print("=" * 80)
        print(f"Case Title / No  : {extraction.case_name}")
        print(f"Order Date       : {extraction.order_date or 'N/A'}")
        print(f"Court / Bench    : {extraction.court_number or 'N/A'}")
        print(f"Coram Judges     : {', '.join(extraction.bench_judges) if extraction.bench_judges else 'N/A'}")
        
        print(f"\n\033[93m📜 Invoked Statutes & Sections ({len(extraction.invoked_statutes)}):\033[0m")
        if not extraction.invoked_statutes:
            print("  • None extracted")
        else:
            for s in extraction.invoked_statutes:
                print(f"  • Section {s.section:<6} of {s.act_name}")

        print(f"\n\033[93m🏛️  Cited Precedents ({len(extraction.cited_precedents)}):\033[0m")
        if not extraction.cited_precedents:
            print("  • None extracted")
        else:
            for p in extraction.cited_precedents:
                print(f"  • {p.case_title} ({p.citation or 'Citation N/A'}) - {p.court}")

        if args.ingest:
            db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
            store = LegalGraphStore(db_path=db_path)
            stats = ingest_order_extraction(store, extraction)
            print(f"\n\033[92m✓ Successfully merged into Knowledge Graph (+{stats['nodes_added']} nodes, +{stats['relations_added']} relations).\033[0m")
            store.close()

    elif args.command == "graph-sync-orders":
        import os
        from lawnidhi.graph.order_sync import sync_all_orders
        from lawnidhi.graph.store import LegalGraphStore

        orders_dir = args.dir or os.path.join(os.path.dirname(__file__), "data", "orders")
        print(f"\n\033[96m🚀 Ingesting all order PDFs from: {orders_dir}...\033[0m")
        
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        summary = sync_all_orders(store, orders_dir)

        print("\n\033[92m📊 Order Sync Summary:\033[0m")
        print("-" * 60)
        print(f"  Total Order PDFs Processed : {summary['processed']} / {summary['total_pdfs']}")
        print(f"  Total Statutes Extracted   : {summary['total_statutes_extracted']}")
        print(f"  Total Precedents Extracted : {summary['total_precedents_extracted']}")
        if summary["errors"]:
            print(f"  Errors Encountered         : {len(summary['errors'])}")
            for err in summary["errors"][:5]:
                print(f"    • {err}")
        store.close()

    elif args.command == "serve":
        import uvicorn
        print(f"\n\033[92m🚀 Starting LawNidhi REST API Server at http://{args.host}:{args.port}...\033[0m")
        print(f"📖 Interactive Swagger Docs: http://{args.host}:{args.port}/docs")
        print(f"📖 ReDoc Documentation   : http://{args.host}:{args.port}/redoc\n")
        uvicorn.run("lawnidhi.server.app:app", host=args.host, port=args.port, reload=args.reload)

    elif args.command == "graph-rag":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        from lawnidhi.rag.vector_store import LegalDocumentStore
        from lawnidhi.rag.hybrid_retriever import HybridGraphRAGRetriever
        from lawnidhi.rag.synthesizer import LegalSynthesizer

        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        orders_dir = os.path.join(os.path.dirname(__file__), "data", "orders")

        print(f"\n\033[96m🔍 Running Hybrid GraphRAG Query: '{args.query}'...\033[0m")
        graph_store = LegalGraphStore(db_path=db_path)
        doc_store = LegalDocumentStore()
        if os.path.isdir(orders_dir):
            doc_store.index_directory(orders_dir)

        retriever = HybridGraphRAGRetriever(doc_store=doc_store, graph_store=graph_store)
        res = retriever.retrieve(args.query, top_k=args.top_k)

        if args.synthesize:
            synthesizer = LegalSynthesizer()
            answer = synthesizer.synthesize(res)
            print(f"\n\033[92m⚖️  Grounded Legal Synthesis:\033[0m")
            print("=" * 80)
            print(answer.answer)
            print("=" * 80)
        else:
            print(f"\n\033[92m📊 Hybrid Retrieval Context:\033[0m")
            print("=" * 80)
            print(res.formatted_context)
            print("=" * 80)

        graph_store.close()

    elif args.command == "graph-communities":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        from lawnidhi.graph.clustering import GraphClusterEngine

        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        engine = GraphClusterEngine(store)

        summary = engine.detect_communities(min_size=args.min_size)
        print(f"\n\033[92m🔮 Thematic Legal Communities (Total Clusters: {summary.total_communities} | Modularity: {summary.modularity_score}):\033[0m")
        print("=" * 95)
        print(f"{'ID':<4} {'Size':<6} {'Cluster Label':<40} {'Top Statutes & Key Hubs'}")
        print("-" * 95)
        for c in summary.communities:
            hubs_str = ", ".join([h["name"] for h in c.top_hubs[:2]])
            stat_str = f"📜 {c.statutes[0]}" if c.statutes else f"👥 {hubs_str}"
            label_disp = c.label[:38]
            print(f"{c.community_id:<4} {c.size:<6} {label_disp:<40} {stat_str}")
        print("=" * 95)
        store.close()

    elif args.command == "ask":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        from lawnidhi.rag.vector_store import LegalDocumentStore
        from lawnidhi.agent.co_counsel import AgenticCoCounsel

        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        graph_store = LegalGraphStore(db_path=db_path)
        doc_store = LegalDocumentStore()
        orders_dir = os.path.join(os.path.dirname(__file__), "data", "orders")
        if os.path.isdir(orders_dir):
            doc_store.index_directory(orders_dir)

        agent = AgenticCoCounsel(graph_store=graph_store, doc_store=doc_store, max_loops=args.max_loops)
        response = agent.run(args.query)

        if args.verbose:
            print(f"\n\033[94m🤖 Agentic Co-Counsel Reasoning Trajectory ({len(response.steps)} loops | {response.execution_time_sec}s):\033[0m")
            print("=" * 80)
            for step in response.steps:
                print(f"\033[1m[Loop {step.loop_index}]\033[0m \033[93mThought:\033[0m {step.thought}")
                if step.action_tool:
                    print(f"  \033[96mAction:\033[0m {step.action_tool}({step.action_input})")
                if step.observation:
                    print(f"  \033[92mObservation:\033[0m {step.observation}")
                print("-" * 80)

        print(f"\n\033[92m⚖️  Agentic Co-Counsel Final Brief / Answer:\033[0m")
        print("=" * 80)
        print(response.final_answer)
        print("=" * 80)
        graph_store.close()

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
