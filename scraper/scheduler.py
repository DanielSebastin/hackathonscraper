"""
scheduler.py — APScheduler job that runs the full data pipeline:
               scrape → clean → embed → upload to Qdrant.

Run directly:
    python -m scraper.scheduler

Or import and call start_scheduler() to run it alongside the API.
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scheduler")

INTERVAL_HOURS = 12  # How often to refresh the database


def run_pipeline():
    """
    Full data refresh pipeline:
    1. Scrape Knowafest
    2. Upload fresh embeddings to Qdrant
    """
    log.info("── Pipeline triggered ──────────────────────────")

    try:
        log.info("Step 1/2: Running scraper...")
        from scraper.scraper import scrape_knowafest
        scrape_knowafest()
        log.info("Step 1/2: Scrape complete.")
    except Exception as e:
        log.error(f"Scraper failed: {e}")
        return

    try:
        log.info("Step 2/2: Uploading embeddings to Qdrant...")
        from database.uploader import seed_database
        seed_database()
        log.info("Step 2/2: Upload complete.")
    except Exception as e:
        log.error(f"Uploader failed: {e}")
        return

    log.info("── Pipeline complete ───────────────────────────")


def start_scheduler(background: bool = False):
    """
    Start the scheduler.
    - background=False → blocks the process (use when running standalone)
    - background=True  → non-blocking (use when embedding into FastAPI startup)
    """
    SchedulerClass = BackgroundScheduler if background else BlockingScheduler
    scheduler = SchedulerClass()

    import datetime
    
    # Schedule recurring job
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        hours=INTERVAL_HOURS,
        id="data_pipeline",
        name="Hackathon Data Refresh",
        replace_existing=True,
        next_run_time=datetime.datetime.now() # Runs immediately, then every INTERVAL_HOURS
    )

    log.info(f"Scheduler started. Pipeline runs every {INTERVAL_HOURS} hours.")

    scheduler.start()
    return scheduler


if __name__ == "__main__":
    log.info("Running pipeline once immediately, then scheduling...")
    start_scheduler(background=False)
