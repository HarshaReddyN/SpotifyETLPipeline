# SpotifyETLPipeline

ETL pipeline that pulls the top featured playlist from every Spotify market, normalises the data into three tables, and loads it into AWS Redshift daily.

## Architecture

```
Spotify API  →  Extract  →  Transform  →  Load  →  Redshift
                (JSON)       (Parquet)    (psycopg2)
```

Three Redshift tables produced each run:
- `spotify_etl.featured_playlists` — one row per playlist per market
- `spotify_etl.playlist_tracks`    — one row per track per playlist per market
- `spotify_etl.track_artists`      — one row per artist per track per market

## Setup

```bash
# 1. Clone and install dependencies
pip install -r requirements.txt

# 2. Set environment variables (copy .env.example → .env)
cp .env.example .env
# edit .env with your credentials

# 3. Run once
python app.py

# 4. Run on daily schedule (06:00 UTC)
python app.py --schedule

# 5. Dry run (no Redshift write)
python app.py --dry-run
```

## Project Structure

```
SpotifyETLPipeline/
├── app.py                          # entrypoint + scheduler
├── config/config.yaml              # all config (env vars injected at runtime)
├── src/Pipeline/
│   ├── extract/__init__.py         # Spotify API client
│   ├── transform/__init__.py       # flatten + clean JSON → DataFrames
│   └── load/__inti__.py            # Redshift upsert
├── utils/__init__.py               # config loader, logger, retry decorator
├── data/
│   ├── raw/<YYYY-MM-DD>/           # raw JSON snapshots
│   └── transformed/<YYYY-MM-DD>/  # parquet audit files
└── logs/pipeline.log
```

## Markets Covered (20)
US, GB, IN, DE, FR, JP, BR, AU, CA, MX, NG, ZA, AR, KR, SE, NL, IT, ES, PL, SG
