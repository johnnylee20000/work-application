"""Scheduler to watch `data/drop/` for new templates and import them automatically.

Runs a periodic job (uses `schedule`) that scans the drop folder and attempts
to import any `.csv` or `.xlsx` files using `import_template_into_db`.

Successful files are moved to `data/processed/` and failures to `data/failed/` with an
error `.log` file alongside.
"""
import os
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path

import schedule


def setup_logger(log_path):
    logger = logging.getLogger("scheduler")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    if not logger.handlers:
        logger.addHandler(fh)
    return logger


def process_file(path, db_path, processed_dir, failed_dir, logger=None):
    from src.collectors import import_template_into_db

    p = Path(path)
    try:
        logger.info(f"Processing file: {p}")
        count = import_template_into_db(str(p), db_path)
        logger.info(f"Imported {count} rows from {p.name}")
        # move to processed with timestamp
        dest = Path(processed_dir) / f"{p.stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{p.suffix}"
        shutil.move(str(p), str(dest))
        logger.info(f"Moved to processed: {dest}")
        return True
    except Exception as e:
        logger.exception(f"Failed to process {p}: {e}")
        # move to failed and write error file
        dest = Path(failed_dir) / f"{p.stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{p.suffix}"
        shutil.move(str(p), str(dest))
        err_log = Path(failed_dir) / f"{p.stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.log"
        with open(err_log, "w") as fh:
            fh.write(str(e))
        return False


def check_and_process(drop_dir, db_path, processed_dir, failed_dir, logger):
    drop = Path(drop_dir)
    for entry in drop.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in (".csv", ".xlsx"):
            logger.info(f"Skipping unsupported file type: {entry.name}")
            continue
        process_file(entry, db_path, processed_dir, failed_dir, logger=logger)


def run_scheduler(db_path="./data/app.db", drop_dir="./data/drop", processed_dir="./data/processed", failed_dir="./data/failed", interval_minutes=1, run_forever=True):
    # ensure folders exist
    os.makedirs(drop_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(failed_dir, exist_ok=True)
    log_path = os.path.join("./data", "scheduler.log")
    logger = setup_logger(log_path)

    logger.info("Starting scheduler")

    # run immediately once
    check_and_process(drop_dir, db_path, processed_dir, failed_dir, logger)

    schedule.every(interval_minutes).minutes.do(check_and_process, drop_dir, db_path, processed_dir, failed_dir, logger)

    if not run_forever:
        # run pending once and return
        schedule.run_pending()
        return

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    run_scheduler()
