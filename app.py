"""
app.py — entrypoint for the Spotify ETL pipeline.

Usage
─────
  # Run once immediately
  python app.py

  # Run on schedule (daily cron defined in config.yaml)
  python app.py --schedule

  # Re-transform + load from existing raw data (no API calls)
  python app.py --skip-extract --raw-dir data/raw/2025-03-17

  # Dry-run: extract + transform only, skip Redshift load
  python app.py --dry-run
"""
import argparse
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from src.Pipeline import Pipeline
from utils import load_config, get_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Spotify ETL Pipeline")
    parser.add_argument("--schedule",      action="store_true",
                        help="Run on the cron schedule defined in config.yaml")
    parser.add_argument("--skip-extract",  action="store_true",
                        help="Skip Spotify API calls; use existing raw JSON")
    parser.add_argument("--raw-dir",       type=str, default=None,
                        help="Path to raw data directory (required with --skip-extract)")
    parser.add_argument("--dry-run",       action="store_true",
                        help="Run extract + transform only; skip Redshift load")
    parser.add_argument("--config",        type=str, default=None,
                        help="Path to alternate config.yaml")
    return parser.parse_args()


def run_pipeline(config: dict, skip_extract: bool, raw_dir: Path, dry_run: bool):
    """Single pipeline execution."""
    if dry_run:
        # Patch config so loader is a no-op
        from unittest.mock import MagicMock
        pipeline = Pipeline(config)
        pipeline.loader.run = MagicMock(return_value=None)
        logger = get_logger("app", config)
        logger.info("DRY RUN — Redshift load is disabled.")
    else:
        pipeline = Pipeline(config)

    pipeline.run(skip_extract=skip_extract, raw_dir=raw_dir)


def main():
    args = parse_args()
    config = load_config(Path(args.config) if args.config else None)
    logger = get_logger("app", config)

    raw_dir = Path(args.raw_dir) if args.raw_dir else None

    if args.schedule:
        cron_expr = config["pipeline"]["schedule_cron"]       # "0 6 * * *"
        minute, hour, dom, month, dow = cron_expr.split()
        scheduler = BlockingScheduler()
        scheduler.add_job(
            run_pipeline,
            trigger="cron",
            hour=hour, minute=minute,
            args=[config, args.skip_extract, raw_dir, args.dry_run],
        )
        logger.info(f"Scheduler started — cron='{cron_expr}' (UTC). Press Ctrl+C to stop.")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
    else:
        run_pipeline(config, args.skip_extract, raw_dir, args.dry_run)


if __name__ == "__main__":
    main()
