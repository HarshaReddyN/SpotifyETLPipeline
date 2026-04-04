"""
Pipeline orchestrator — wires Extract → Transform → Load together.

Import and call Pipeline(config).run() or use app.py for scheduling.
"""
from pathlib import Path

from src.Pipeline.extract import SpotifyExtractor
from src.Pipeline.transform import SpotifyTransformer
from src.Pipeline.load.__inti__ import RedshiftLoader   # preserving original filename
from utils import get_logger


class Pipeline:
    """Top-level orchestrator for the Spotify ETL pipeline."""

    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger("pipeline", config)
        self.extractor   = SpotifyExtractor(config)
        self.transformer = SpotifyTransformer(config)
        self.loader      = RedshiftLoader(config)

    def run(self, skip_extract: bool = False, raw_dir: Path = None):
        """
        Execute the full ETL cycle.

        Args:
            skip_extract:  If True, skip the API calls and re-use an existing raw_dir.
            raw_dir:       Must be provided when skip_extract=True.
        """
        self.logger.info("=" * 60)
        self.logger.info("Spotify ETL pipeline starting")
        self.logger.info("=" * 60)

        # ── Extract ────────────────────────────────────────────────
        if skip_extract:
            if raw_dir is None:
                raise ValueError("raw_dir must be provided when skip_extract=True")
            self.logger.info(f"Skipping extract — using raw_dir={raw_dir}")
        else:
            raw_dir = self.extractor.run()

        # ── Transform ──────────────────────────────────────────────
        dfs = self.transformer.run(raw_dir)

        # ── Load ───────────────────────────────────────────────────
        self.loader.run(dfs)

        self.logger.info("Pipeline finished successfully.")
        return dfs
