# Workload Automation — Prototype

Prototype to collect data from Excel files, databases, and manual inputs, store them in SQLite, and produce basic statistical reports and charts.

Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Edit `.env.example` to set `DB_PATH`, copy to `.env`.

3. Run the main script for help:

```bash
python main.py --help
```

Prototype structure

- `src/collectors.py` — functions to load Excel, CSV, and database extracts
- `src/storage.py` — save dataframes to SQLite
- `src/reports.py` — summary statistics and simple charts
- `main.py` — small CLI to run tasks

New commands added

- Create a template:

```bash
python main.py template data/new_cases.csv
```

- Import a filled template into the DB:

```bash
python main.py import-template data/new_cases.csv --db data/app.db
```

- Add a single case interactively from the terminal:

```bash
python main.py add --db data/app.db
```

- Generate aggregated case reports and charts:

```bash
python main.py report-cases --db data/app.db --out-csv cases_summary.csv --out-prefix cases_report
```

The `add` interactive command now asks you to choose from a short controlled vocabulary for `court_heard_in` (you can also type a custom court name).

Scheduler (auto-import)

You can run a scheduler that watches `data/drop/` and automatically imports any `.csv` or `.xlsx` template files. Files that successfully import are moved to `data/processed/`; files that fail are moved to `data/failed/` and an error log is written.

Start the scheduler from the project root:

```bash
python main.py run-scheduler --db data/app.db --drop data/drop --processed data/processed --failed data/failed --interval 1
```

Drop files into `data/drop/` (CSV or XLSX). The scheduler polls every `--interval` minutes (default 1).

Scheduler logs are written to `data/scheduler.log`.

Docker (optional)

An example `Dockerfile` is included to run the scheduler in a container. If you use the Dockerfile, mount a host folder to `/app/data` so files persist and you can drop templates into `data/drop/`.

Example run with a mounted data folder:

```bash
docker build -t work-application:latest .
docker run --rm -v $(pwd)/data:/app/data work-application:latest python main.py run-scheduler --db data/app.db --drop data/drop --processed data/processed --failed data/failed --interval 1
```


Next steps

- Add authentication for protected databases or APIs
- Add scheduled runs (cron or Docker + schedule)
- Expand tests and CI
# work-application
this work application is to automate most of my work processes and calculate statistical data based on the the books and registers i use everyday  
