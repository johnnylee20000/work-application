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

CI / Deploy

This repository includes a GitHub Actions workflow at `.github/workflows/ci-deploy.yml` that will:

- Run `pytest` on each push to `main`.
- Build and push a Docker image to GitHub Container Registry (GHCR) as `ghcr.io/<OWNER>/work-application:latest` and a SHA-tagged image.
- If the following repository Secrets are set, it will SSH to your host and deploy the latest image:

Required secrets for automated deploy (set in repository -> Settings -> Secrets):
- `DEPLOY_SSH_KEY` — private SSH key (no passphrase) with access to the deploy host.
- `DEPLOY_HOST` — host IP or hostname where container will run.
- `DEPLOY_USER` — username to SSH as on the host.

Optional:
- `DEPLOY_DATA_DIR` — path on the host to bind to `/app/data` (defaults to `/home/<DEPLOY_USER>/work-application-data`).

If your GHCR image is private (the default for organization packages), add these additional secrets so the host can authenticate to GHCR before pulling:

- `GHCR_USER` — your GitHub username or organization that owns the package.
- `GHCR_PAT` — a Personal Access Token with the `read:packages` scope (and `write:packages` if you also push from CI).

Create a GHCR PAT:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) or the newer token UI.
2. Create a token with at least `read:packages` (and `write:packages` if needed).
3. Add the token value as a repository secret named `GHCR_PAT`, and set `GHCR_USER` to your GitHub username/org.


Notes:
- The workflow uses `GITHUB_TOKEN` to authenticate to GHCR for pushes. Ensure your org settings allow `GITHUB_TOKEN` package write if publishing to GHCR for org-owned repos.
- The SSH deploy step assumes Docker is installed on the host and the `docker` CLI is available to the SSH user.

Manual deploy alternative

You can also deploy manually using the included `deploy/docker-compose.yml` (replace `<OWNER>` with your GitHub user/org and ensure `data/` is mounted):

```bash
scp deploy/docker-compose.yml deploy@your-host:~/work-application/docker-compose.yml
ssh deploy@your-host 'mkdir -p ~/work-application/data'
ssh deploy@your-host 'docker pull ghcr.io/<OWNER>/work-application:latest'
ssh deploy@your-host 'cd ~/work-application && docker compose up -d'
```



Next steps

- Add authentication for protected databases or APIs
- Add scheduled runs (cron or Docker + schedule)
- Expand tests and CI
# work-application
this work application is to automate most of my work processes and calculate statistical data based on the the books and registers i use everyday  
