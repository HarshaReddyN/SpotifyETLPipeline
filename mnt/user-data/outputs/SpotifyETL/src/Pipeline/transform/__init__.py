"""
Transform layer — flatten and clean raw Spotify JSON into three normalised tables.

Output schema
─────────────
featured_playlists   (playlist_id PK, market, name, description, owner_id,
                      owner_name, followers, snapshot_id, track_count,
                      is_collaborative, is_public, external_url, image_url,
                      run_date)

playlist_tracks      (row_id PK, playlist_id FK, track_id, added_at,
                      track_name, duration_ms, duration_min, explicit,
                      popularity, album_id, album_name, album_release_date,
                      market, run_date)

track_artists        (row_id PK, track_id FK, artist_id, artist_name,
                      market, run_date)
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from utils import get_logger


class SpotifyTransformer:
    """Reads raw JSON from the extract layer and emits clean DataFrames."""

    def __init__(self, config: dict):
        self.pipeline_cfg = config["pipeline"]
        self.logger = get_logger("transform", config)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _make_row_id(*parts) -> str:
        """Deterministic surrogate key from concatenated parts."""
        key = "|".join(str(p) for p in parts)
        return hashlib.md5(key.encode()).hexdigest()

    @staticmethod
    def _safe_str(val, max_len: int = 500) -> str:
        if val is None:
            return ""
        return str(val)[:max_len]

    # ------------------------------------------------------------------ transform playlists
    def transform_playlists(self, raw: list[dict], run_date: str) -> pd.DataFrame:
        rows = []
        for p in raw:
            if not p or not p.get("id"):
                continue
            rows.append({
                "playlist_id":     p.get("id", ""),
                "market":          p.get("_market", ""),
                "name":            self._safe_str(p.get("name"), 200),
                "description":     self._safe_str(p.get("description"), 500),
                "owner_id":        (p.get("owner") or {}).get("id", ""),
                "owner_name":      self._safe_str((p.get("owner") or {}).get("display_name"), 200),
                "followers":       (p.get("followers") or {}).get("total", 0),
                "snapshot_id":     p.get("snapshot_id", ""),
                "track_count":     (p.get("tracks") or {}).get("total", 0),
                "is_collaborative": bool(p.get("collaborative", False)),
                "is_public":       bool(p.get("public", True)),
                "external_url":    (p.get("external_urls") or {}).get("spotify", ""),
                "image_url":       (p.get("images") or [{}])[0].get("url", ""),
                "run_date":        run_date,
            })
        df = pd.DataFrame(rows).drop_duplicates(subset=["playlist_id", "market"])
        self.logger.info(f"Playlists transformed: {len(df)} rows")
        return df

    # ------------------------------------------------------------------ transform tracks
    def transform_tracks(self, raw: list[dict], run_date: str) -> pd.DataFrame:
        rows = []
        for item in raw:
            track = item.get("track")
            if not track or not track.get("id"):
                continue
            duration_ms = track.get("duration_ms", 0)
            rows.append({
                "row_id":              self._make_row_id(
                                           item.get("_playlist_id"),
                                           track.get("id"),
                                           item.get("_market")
                                       ),
                "playlist_id":         item.get("_playlist_id", ""),
                "track_id":            track.get("id", ""),
                "added_at":            item.get("added_at", ""),
                "track_name":          self._safe_str(track.get("name"), 300),
                "duration_ms":         duration_ms,
                "duration_min":        round(duration_ms / 60000, 2),
                "explicit":            bool(track.get("explicit", False)),
                "popularity":          int(track.get("popularity", 0)),
                "album_id":            (track.get("album") or {}).get("id", ""),
                "album_name":          self._safe_str(
                                           (track.get("album") or {}).get("name"), 300),
                "album_release_date":  (track.get("album") or {}).get("release_date", ""),
                "market":              item.get("_market", ""),
                "run_date":            run_date,
            })
        df = pd.DataFrame(rows).drop_duplicates(subset=["row_id"])
        # coerce types
        df["added_at"] = pd.to_datetime(df["added_at"], errors="coerce", utc=True)
        df["popularity"] = df["popularity"].clip(0, 100)
        self.logger.info(f"Tracks transformed: {len(df)} rows")
        return df

    # ------------------------------------------------------------------ transform artists
    def transform_artists(self, raw_tracks: list[dict], run_date: str) -> pd.DataFrame:
        rows = []
        for item in raw_tracks:
            track = item.get("track")
            if not track:
                continue
            for artist in (track.get("artists") or []):
                rows.append({
                    "row_id":      self._make_row_id(
                                       track.get("id"),
                                       artist.get("id"),
                                       item.get("_market")
                                   ),
                    "track_id":    track.get("id", ""),
                    "artist_id":   artist.get("id", ""),
                    "artist_name": self._safe_str(artist.get("name"), 200),
                    "market":      item.get("_market", ""),
                    "run_date":    run_date,
                })
        df = pd.DataFrame(rows).drop_duplicates(subset=["row_id"])
        self.logger.info(f"Artists transformed: {len(df)} rows")
        return df

    # ------------------------------------------------------------------ run
    def run(self, raw_dir: Path) -> dict[str, pd.DataFrame]:
        """
        Read raw JSON from extract step, return dict of clean DataFrames.
        Also persists parquet snapshots under data/transformed/<run_date>/.
        """
        run_date = raw_dir.name                     # folder name is the run date
        self.logger.info(f"Starting transform for run_date={run_date}")

        raw_playlists = json.loads((raw_dir / "playlists.json").read_text())
        raw_tracks    = json.loads((raw_dir / "tracks.json").read_text())

        dfs = {
            "featured_playlists": self.transform_playlists(raw_playlists, run_date),
            "playlist_tracks":    self.transform_tracks(raw_tracks, run_date),
            "track_artists":      self.transform_artists(raw_tracks, run_date),
        }

        # persist parquet for audit / re-load capability
        transformed_dir = (
            Path(self.pipeline_cfg["data_dir"])
            / self.pipeline_cfg["transformed_subdir"]
            / run_date
        )
        transformed_dir.mkdir(parents=True, exist_ok=True)
        for name, df in dfs.items():
            df.to_parquet(transformed_dir / f"{name}.parquet", index=False)

        self.logger.info(f"Transform complete. Parquet written to {transformed_dir}")
        return dfs
