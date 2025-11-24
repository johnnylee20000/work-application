import argparse
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Workload automation prototype")
    sub = parser.add_subparsers(dest="cmd")

    p_excel = sub.add_parser("excel", help="Load from Excel file")
    p_excel.add_argument("path")
    p_excel.add_argument("--sheet", default=None)

    p_csv = sub.add_parser("manual", help="Load manual CSV")
    p_csv.add_argument("path")

    p_db = sub.add_parser("db", help="Load from DB via SQL query")
    p_db.add_argument("query")
    p_db.add_argument("--conn", default=os.getenv("DB_CONN"))

    p_report = sub.add_parser("report", help="Generate report from CSV or table")
    p_report.add_argument("path")
    p_report.add_argument("--out", default="report_summary.csv")

    p_template = sub.add_parser("template", help="Create new case template CSV/XLSX")
    p_template.add_argument("path", help="Output path for the template file")
    p_template.add_argument("--format", choices=["csv","xlsx"], default=None, help="File format to create (csv or xlsx)")
    p_import = sub.add_parser("import-template", help="Import a filled template CSV/XLSX into the DB")
    p_import.add_argument("path", help="Path to filled template file")
    p_import.add_argument("--db", default=os.getenv("DB_PATH", "./data/app.db"), help="DB path (overrides env)")

    p_add = sub.add_parser("add", help="Interactively add a single case row")
    p_add.add_argument("--db", default=os.getenv("DB_PATH", "./data/app.db"), help="DB path (overrides env)")
    p_report_cases = sub.add_parser("report-cases", help="Generate aggregated case reports and charts")
    p_report_cases.add_argument("--db", default=os.getenv("DB_PATH", "./data/app.db"), help="DB path (overrides env)")
    p_report_cases.add_argument("--out-csv", default="cases_summary.csv", help="Output summary CSV path")
    p_report_cases.add_argument("--out-prefix", default="cases_report", help="Output prefix for per-chart files")
    p_run_scheduler = sub.add_parser("run-scheduler", help="Run the file-drop scheduler to auto-import templates")
    p_run_scheduler.add_argument("--db", default=os.getenv("DB_PATH", "./data/app.db"), help="DB path (overrides env)")
    p_run_scheduler.add_argument("--drop", default="./data/drop", help="Drop folder to watch")
    p_run_scheduler.add_argument("--processed", default="./data/processed", help="Processed files folder")
    p_run_scheduler.add_argument("--failed", default="./data/failed", help="Failed files folder")
    p_run_scheduler.add_argument("--interval", type=int, default=1, help="Poll interval in minutes")

    args = parser.parse_args()

    if args.cmd == "excel":
        from src.collectors import load_excel
        from src.storage import save_dataframe_to_sqlite
        df = load_excel(args.path, sheet_name=args.sheet)
        db_path = os.getenv("DB_PATH", "./data/app.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        save_dataframe_to_sqlite(df, "excel_import", db_path)
        print("Saved Excel to database")

    elif args.cmd == "manual":
        from src.collectors import load_manual_csv
        from src.storage import save_dataframe_to_sqlite
        df = load_manual_csv(args.path)
        db_path = os.getenv("DB_PATH", "./data/app.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        save_dataframe_to_sqlite(df, "manual_inputs", db_path)
        print("Saved manual CSV to database")

    elif args.cmd == "db":
        from src.collectors import load_from_db
        from src.reports import generate_summary, save_summary_csv
        conn = args.conn
        if not conn:
            print("No connection string provided. Set DB_CONN env or use --conn.")
            return
        df = load_from_db(args.query, conn)
        summary = generate_summary(df)
        save_summary_csv(summary, "db_query_summary.csv")
        print("Saved DB query summary to db_query_summary.csv")

    elif args.cmd == "report":
        import pandas as pd
        from src.reports import generate_summary, save_summary_csv, plot_numeric_histograms
        df = pd.read_csv(args.path)
        summary = generate_summary(df)
        save_summary_csv(summary, args.out)
        plot_numeric_histograms(df, args.out.replace('.csv',''))
        print(f"Report saved to {args.out} and plots created")

    elif args.cmd == "template":
        from src.collectors import create_case_template
        out_path = args.path
        fmt = args.format if args.format else ("xlsx" if out_path.lower().endswith("xlsx") else "csv")
        create_case_template(out_path, file_format=fmt)
        print(f"Created template file: {out_path}")

    elif args.cmd == "import-template":
        from src.collectors import import_template_into_db
        db_path = args.db
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        try:
            count = import_template_into_db(args.path, db_path)
            print(f"Imported {count} rows into database {db_path}")
        except Exception as e:
            print(f"Import failed: {e}")

    elif args.cmd == "add":
        # Interactive prompts
        from src.storage import init_cases_table, insert_cases_from_df
        import pandas as pd
        db_path = args.db
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        fields = [
            ("date", "Date (YYYY-MM-DD)"),
            ("complainant", "Complainant"),
            ("accused", "Accused"),
            ("offences", "Offences"),
            ("subject", "Subject"),
            # court_heard_in handled separately as a controlled list
            ("submitted", "Submitted? (yes/no)"),
            ("submitted_documents", "Submitted documents (comma-separated)"),
            ("last_court_date", "Last court date (YYYY-MM-DD)"),
            ("next_court_date", "Next court date (YYYY-MM-DD)"),
        ]
        row = {}
        for key, prompt in fields:
            val = input(f"{prompt}: ")
            row[key] = val if val != "" else None

        # Controlled vocabulary for court_heard_in
        court_options = ["Magistrates Court", "High Court", "Family Court", "Local Court", "Other"]
        print("Select where the court matter is heard:")
        for i, opt in enumerate(court_options, start=1):
            print(f"{i}. {opt}")
        sel = input("Choose number (or type a custom name): ")
        court_val = None
        try:
            idx = int(sel)
            if 1 <= idx <= len(court_options):
                if court_options[idx-1] == "Other":
                    court_val = input("Enter court name: ")
                else:
                    court_val = court_options[idx-1]
            else:
                court_val = sel
        except Exception:
            court_val = sel

        row["court_heard_in"] = court_val if court_val != "" else None

        df = pd.DataFrame([row])
        try:
            init_cases_table(db_path)
            insert_cases_from_df(df, db_path)
            print("Added case to DB")
        except Exception as e:
            print(f"Failed to add case: {e}")

    elif args.cmd == "report-cases":
        from src.reports import aggregate_cases_report
        db_path = args.db
        try:
            out_csv, plots = aggregate_cases_report(db_path, out_csv=args.out_csv, out_prefix=args.out_prefix)
            print(f"Report written to {out_csv}")
            if plots:
                print("Generated plots:")
                for p in plots:
                    print(f" - {p}")
        except Exception as e:
            print(f"Failed to generate reports: {e}")

    elif args.cmd == "run-scheduler":
        from scripts.scheduler import run_scheduler
        db_path = args.db
        drop = args.drop
        processed = args.processed
        failed = args.failed
        interval = args.interval
        print(f"Starting scheduler: watching {drop} every {interval} minute(s). Ctrl+C to stop.")
        run_scheduler(db_path=db_path, drop_dir=drop, processed_dir=processed, failed_dir=failed, interval_minutes=interval)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
