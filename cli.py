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
    \033[96mgraph-daily-board\033[0m       - View daily courtroom cause list board
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
    gdb_parser.add_argument("date", help="Hearing date (YYYY-MM-DD)")
    gdb_parser.add_argument("--court", default=None, help="Optional court number filter (e.g. 'Court 1')")

    gcc_parser = subparsers.add_parser("graph-counsel-clashes", help="Detect courtroom scheduling clashes for a counsel")
    gcc_parser.add_argument("date", help="Hearing date (YYYY-MM-DD)")
    gcc_parser.add_argument("counsel", default=None, nargs="?", help="Counsel name (default: from config)")

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
        from lawnidhi.graph.store import LegalGraphStore
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        cases = store.get_cases_listed_on_date(args.date, court_no=args.court)
        if not cases:
            print(f"No cases listed on {args.date} in the Knowledge Graph.")
        else:
            court_header = f" ({args.court})" if args.court else ""
            print(f"\n\033[92m📋 Daily Board for {args.date}{court_header} (Total Items: {len(cases)})\033[0m")
            print("-" * 85)
            print(f"{'Item':<6} {'Court':<10} {'Case Title / Number':<40} {'Judge'}")
            print("-" * 85)
            for c in cases:
                case_title = (c['case_name'][:38] + '..') if len(c['case_name']) > 40 else c['case_name']
                judge_title = (c['judge_name'][:25] + '..') if len(c['judge_name']) > 27 else (c['judge_name'] or '-')
                print(f"{c['item_number']:<6} {c['court_no']:<10} {case_title:<40} {judge_title}")
        store.close()

    elif args.command == "graph-counsel-clashes":
        import os
        from lawnidhi.graph.store import LegalGraphStore
        counsel_name = args.counsel or config.get_counsel_name()
        db_path = os.path.join(os.path.dirname(__file__), "data", "lawnidhi_graph", "kuzu_db")
        store = LegalGraphStore(db_path=db_path)
        clashes = store.find_counsel_clashes(args.date, counsel_name)
        if not clashes:
            print(f"\n\033[92m✓ No courtroom clashes detected for '{counsel_name}' on {args.date}.\033[0m")
        else:
            print(f"\n\033[91m⚠️  COURTROOM CLASH DETECTED for '{counsel_name}' on {args.date}!\033[0m")
            print("-" * 75)
            for c in clashes:
                print(f"  • {c['court_no']} | Item {c.get('item_number') or '-'}: {c['case_name']} (Judge: {c['judge_name']})")
        store.close()

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
