"""
src/Pipeline/load/__init__.py

Loads the transformed DataFrames into the configured target.
Supports:
  - AWS Redshift  (via psycopg2 + COPY from S3, or direct INSERT for small sets)
  - PostgreSQL    (via psycopg2)
  - CSV           (local fallback, great for development)

Target tables follow the star schema defined in the transform module.
All loaders use UPSERT semantics (INSERT … ON CONFLICT DO NOTHING) so the
pipeline is safe to re-run for the same date.
"""
import io
from pathlib import Path

import pandas as pd

from utils import get_logger

logger = get_logger("load")


# ── Schema DDL ─────────────────────────────────────────────────────────────────

DDL = {
    "dim_run": """
        CREATE TABLE IF NOT EXISTS {schema}.dim_run (
            run_id         VARCHAR(12)   PRIMARY KEY,
            run_date       DATE          NOT NULL,
            run_ts         TIMESTAMPTZ,
            total_markets  INTEGER
        );
    """,
    "dim_market": """
        CREATE TABLE IF NOT EXISTS {schema}.dim_market (
            market_code    VARCHAR(2)    PRIMARY KEY
        );
    """,
    "dim_playlist": """
        CREATE TABLE IF NOT EXISTS {schema}.dim_playlist (
            playlist_id    VARCHAR(64)   PRIMARY KEY,
            name           VARCHAR(512),
            description    TEXT,
            owner          VARCHAR(256),
            snapshot_id    VARCHAR(128),
            external_url   VARCHAR(512),
            image_url      VARCHAR(512),
            total_tracks   INTEGER
        );
    """,
    "dim_track": """
        CREATE TABLE IF NOT EXISTS {schema}.dim_track (
            track_id       VARCHAR(64)   PRIMARY KEY,
            name           VARCHAR(512),
            artist_names   VARCHAR(1024),
            album          VARCHAR(512),
            album_type     VARCHAR(64),
            release_date   VARCHAR(32),
            duration_ms    INTEGER,
            explicit       BOOLEAN,
            popularity     INTEGER,
            isrc           VARCHAR(32),
            preview_url    VARCHAR(512),
            spotify_url    VARCHAR(512)
        );
    """,
    "fact_playlist_tracks": """
        CREATE TABLE IF NOT EXISTS {schema}.fact_playlist_tracks (
            run_id          VARCHAR(12)   NOT NULL,
            run_date        DATE          NOT NULL,
            market          VARCHAR(2)    NOT NULL,
            playlist_id     VARCHAR(64)   NOT NULL,
            track_id        VARCHAR(64)   NOT NULL,
            track_position  INTEGER       NOT NULL,
            added_at        TIMESTAMPTZ,
            added_by        VARCHAR(256),
            PRIMARY KEY (run_id, market, playlist_id, track_id, track_position)
        );
    """,
}

# Load order matters — foreign key respect
LOAD_ORDER = ["dim_run", "dim_market", "dim_playlist", "dim_track", "fact_playlist_tracks"]


# ── CSV Loader ─────────────────────────────────────────────────────────────────

def load_csv(frames: dict[str, pd.DataFrame], output_dir: str) -> None:
    """
    Write each DataFrame to a timestamped CSV file.
    Safe for local development — no DB required.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    run_date = frames["dim_run"]["run_date"].iloc[0]
    for name in LOAD_ORDER:
        df = frames.get(name)
        if df is None or df.empty:
            logger.warning(f"  Skipping {name}: empty DataFrame.")
            continue
        path = out / f"{run_date}_{name}.csv"
        df.to_csv(path, index=False)
        logger.info(f"  CSV → {path}  ({len(df):,} rows)")


# ── PostgreSQL / Redshift Loader ───────────────────────────────────────────────

def _get_connection(db_cfg: dict):
    """Return a psycopg2 connection from db config dict."""
    try:
        import psycopg2
    except ImportError:
        raise ImportError(
            "psycopg2 is required for Postgres/Redshift loading. "
            "Install it with: pip install psycopg2-binary"
        )
    return psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg.get("port", 5432),
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        connect_timeout=30,
    )


def _ensure_schema(cursor, schema: str) -> None:
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")


def _ensure_table(cursor, table: str, schema: str) -> None:
    ddl = DDL[table].format(schema=schema)
    cursor.execute(ddl)


def _upsert_df(cursor, df: pd.DataFrame, table: str, schema: str) -> None:
    """
    Bulk insert using psycopg2 copy_expert (fast) then de-duplicate via
    INSERT … ON CONFLICT DO NOTHING for idempotent re-runs.
    """
    if df.empty:
        return

    # Write to an in-memory CSV buffer
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)

    qualified = f"{schema}.{table}"
    cols = ", ".join(df.columns)

    # Create a temp staging table
    cursor.execute(f"CREATE TEMP TABLE _stage_{table} (LIKE {qualified});")
    cursor.copy_expert(
        f"COPY _stage_{table} ({cols}) FROM STDIN WITH CSV NULL AS '\\N'",
        buf,
    )
    cursor.execute(f"""
        INSERT INTO {qualified} ({cols})
        SELECT {cols} FROM _stage_{table}
        ON CONFLICT DO NOTHING;
    """)
    cursor.execute(f"DROP TABLE _stage_{table};")
    logger.debug(f"  Upserted {len(df):,} rows → {qualified}")


def load_postgres(frames: dict[str, pd.DataFrame], db_cfg: dict) -> None:
    """
    Load all frames into PostgreSQL (also works for Redshift via psycopg2).
    """
    schema = db_cfg.get("schema", "spotify")
    logger.info(f"Connecting to Postgres at {db_cfg['host']}:{db_cfg.get('port', 5432)}")

    conn = _get_connection(db_cfg)
    conn.autocommit = False
    cursor = conn.cursor()

    try:
        _ensure_schema(cursor, schema)
        for table in LOAD_ORDER:
            df = frames.get(table)
            if df is None or df.empty:
                logger.warning(f"  Skipping {table}: empty.")
                continue
            logger.info(f"  Loading {table} ({len(df):,} rows)…")
            _ensure_table(cursor, table, schema)
            _upsert_df(cursor, df, table, schema)
        conn.commit()
        logger.info("All tables loaded successfully.")
    except Exception as exc:
        conn.rollback()
        logger.error(f"Load failed, transaction rolled back: {exc}")
        raise
    finally:
        cursor.close()
        conn.close()


# ── Orchestrated load run ─────────────────────────────────────────────────────

def run_load(frames: dict[str, pd.DataFrame], config: dict) -> None:
    """
    Entry point.  Routes to the correct loader based on config['database']['type'].
    """
    db_type = config["database"]["type"].lower()
    logger.info(f"Loading data → target: {db_type}")

    if db_type == "csv":
        out_dir = config["database"].get(
            "csv_output_dir",
            config["pipeline"]["processed_data_dir"],
        )
        load_csv(frames, out_dir)

    elif db_type in ("postgres", "postgresql", "redshift"):
        load_postgres(frames, config["database"])

    else:
        raise ValueError(
            f"Unknown database type '{db_type}'. "
            "Valid options: csv | postgres | redshift"
        )
