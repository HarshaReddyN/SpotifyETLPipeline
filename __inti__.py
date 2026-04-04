"""
Load layer — upsert clean DataFrames into AWS Redshift.

Strategy
─────────
• Uses psycopg2 (Redshift is Postgres-compatible).
• CREATE TABLE IF NOT EXISTS on first run.
• DELETE matching (playlist_id / run_date) rows, then bulk INSERT via
  execute_values — safe for daily incremental loads without S3 COPY.
• Falls back gracefully on schema drift (logs warning, does not crash).
"""
import io
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from utils import get_logger


# ── DDL ────────────────────────────────────────────────────────────────────────
_DDL = {
    "featured_playlists": """
        CREATE TABLE IF NOT EXISTS {schema}.featured_playlists (
            playlist_id       VARCHAR(64)   NOT NULL,
            market            VARCHAR(8)    NOT NULL,
            name              VARCHAR(200),
            description       VARCHAR(500),
            owner_id          VARCHAR(64),
            owner_name        VARCHAR(200),
            followers         INTEGER       DEFAULT 0,
            snapshot_id       VARCHAR(128),
            track_count       INTEGER       DEFAULT 0,
            is_collaborative  BOOLEAN       DEFAULT FALSE,
            is_public         BOOLEAN       DEFAULT TRUE,
            external_url      VARCHAR(300),
            image_url         VARCHAR(500),
            run_date          DATE          NOT NULL,
            loaded_at         TIMESTAMP     DEFAULT GETDATE(),
            PRIMARY KEY (playlist_id, market, run_date)
        ) DISTSTYLE KEY DISTKEY(market) SORTKEY(run_date);
    """,

    "playlist_tracks": """
        CREATE TABLE IF NOT EXISTS {schema}.playlist_tracks (
            row_id             VARCHAR(32)   NOT NULL PRIMARY KEY,
            playlist_id        VARCHAR(64)   NOT NULL,
            track_id           VARCHAR(64)   NOT NULL,
            added_at           TIMESTAMPTZ,
            track_name         VARCHAR(300),
            duration_ms        INTEGER,
            duration_min       DECIMAL(7,2),
            explicit           BOOLEAN       DEFAULT FALSE,
            popularity         SMALLINT,
            album_id           VARCHAR(64),
            album_name         VARCHAR(300),
            album_release_date VARCHAR(20),
            market             VARCHAR(8)    NOT NULL,
            run_date           DATE          NOT NULL,
            loaded_at          TIMESTAMP     DEFAULT GETDATE()
        ) DISTSTYLE KEY DISTKEY(market) SORTKEY(run_date, playlist_id);
    """,

    "track_artists": """
        CREATE TABLE IF NOT EXISTS {schema}.track_artists (
            row_id       VARCHAR(32)   NOT NULL PRIMARY KEY,
            track_id     VARCHAR(64)   NOT NULL,
            artist_id    VARCHAR(64)   NOT NULL,
            artist_name  VARCHAR(200),
            market       VARCHAR(8)    NOT NULL,
            run_date     DATE          NOT NULL,
            loaded_at    TIMESTAMP     DEFAULT GETDATE()
        ) DISTSTYLE KEY DISTKEY(market) SORTKEY(run_date);
    """,
}


class RedshiftLoader:
    """Manages connection lifecycle and upsert logic for Redshift."""

    def __init__(self, config: dict):
        self.cfg = config["redshift"]
        self.schema = self.cfg["schema"]
        self.tables = self.cfg["tables"]
        self.logger = get_logger("load", config)
        self._conn = None

    # ------------------------------------------------------------------ connection
    def _connect(self):
        if self._conn and not self._conn.closed:
            return
        self.logger.info(f"Connecting to Redshift: {self.cfg['host']}:{self.cfg['port']}")
        self._conn = psycopg2.connect(
            host=self.cfg["host"],
            port=self.cfg["port"],
            dbname=self.cfg["dbname"],
            user=self.cfg["user"],
            password=self.cfg["password"],
            connect_timeout=30,
        )
        self._conn.autocommit = False

    def _cursor(self):
        self._connect()
        return self._conn.cursor()

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            self.logger.info("Redshift connection closed.")

    # ------------------------------------------------------------------ schema setup
    def ensure_schema(self):
        with self._cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema};")
        self._conn.commit()
        self.logger.info(f"Schema '{self.schema}' ensured.")

    def ensure_tables(self):
        with self._cursor() as cur:
            for logical_name, ddl in _DDL.items():
                physical = self.tables.get(logical_name, logical_name)
                sql = ddl.replace("{schema}", self.schema).replace(
                    logical_name, physical
                )
                cur.execute(sql)
        self._conn.commit()
        self.logger.info("All tables ensured.")

    # ------------------------------------------------------------------ upsert
    def _upsert(self, cur, df: pd.DataFrame, table: str, delete_key_col: str):
        """
        Delete rows matching today's run_date + delete_key_col values,
        then bulk insert. Idempotent for daily re-runs.
        """
        if df.empty:
            self.logger.warning(f"Empty DataFrame for {table} — skipping.")
            return

        run_date = df["run_date"].iloc[0]
        ids = tuple(df[delete_key_col].unique())

        del_sql = (
            f"DELETE FROM {self.schema}.{table} "
            f"WHERE run_date = %s AND {delete_key_col} = ANY(%s);"
        )
        cur.execute(del_sql, (run_date, list(ids)))
        self.logger.info(f"Deleted stale rows from {table} for run_date={run_date}")

        # replace NaT/NaN with None for psycopg2
        df = df.where(pd.notnull(df), None)
        cols = list(df.columns)
        rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

        insert_sql = (
            f"INSERT INTO {self.schema}.{table} ({', '.join(cols)}) VALUES %s"
        )
        execute_values(cur, insert_sql, rows, page_size=500)
        self.logger.info(f"Inserted {len(rows)} rows into {table}")

    # ------------------------------------------------------------------ run
    def run(self, dfs: dict[str, pd.DataFrame]):
        """Load all three DataFrames into Redshift."""
        self._connect()
        self.ensure_schema()
        self.ensure_tables()

        mapping = [
            ("featured_playlists", self.tables["playlists"],  "playlist_id"),
            ("playlist_tracks",    self.tables["tracks"],     "playlist_id"),
            ("track_artists",      self.tables["artists"],    "track_id"),
        ]

        try:
            with self._cursor() as cur:
                for logical_name, physical_table, key_col in mapping:
                    self._upsert(cur, dfs[logical_name], physical_table, key_col)
            self._conn.commit()
            self.logger.info("Load complete — transaction committed.")
        except Exception:
            self._conn.rollback()
            self.logger.exception("Load failed — transaction rolled back.")
            raise
        finally:
            self.close()
