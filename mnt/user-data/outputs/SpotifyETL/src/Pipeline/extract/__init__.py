"""
Extract layer — Spotify API client.

Responsibilities:
  1. OAuth2 Client Credentials token fetch (auto-refresh on expiry).
  2. GET /browse/featured-playlists for every configured market.
  3. GET /playlists/{id}/tracks for each playlist returned.
  4. Persist raw JSON responses under data/raw/<run_date>/.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from utils import get_logger, retry


class SpotifyExtractor:
    """Wraps Spotify Web API interactions for the ETL pipeline."""

    def __init__(self, config: dict):
        self.cfg = config["spotify"]
        self.pipeline_cfg = config["pipeline"]
        self.logger = get_logger("extract", config)
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------ auth
    @retry(max_retries=3, backoff_factor=2, exceptions=(requests.HTTPError,))
    def _fetch_token(self) -> str:
        """Request a fresh Client Credentials OAuth token."""
        resp = requests.post(
            self.cfg["token_url"],
            data={"grant_type": "client_credentials"},
            auth=(self.cfg["client_id"], self.cfg["client_secret"]),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data["expires_in"] - 60   # 60s buffer
        self.logger.info("Spotify token refreshed.")
        return self._token

    def _get_token(self) -> str:
        """Return cached token, refreshing if expired."""
        if not self._token or time.time() >= self._token_expiry:
            self._fetch_token()
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    # ------------------------------------------------------------------ API calls
    @retry(max_retries=3, backoff_factor=2, exceptions=(requests.HTTPError,))
    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.cfg['base_url']}/{endpoint.lstrip('/')}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(self.cfg.get("request_delay_seconds", 0.25))
        return resp.json()

    def fetch_featured_playlists(self, market: str) -> list[dict]:
        """Return all featured playlist stubs for a given market."""
        self.logger.info(f"Fetching featured playlists for market={market}")
        data = self._get("browse/featured-playlists", params={"country": market, "limit": 50})
        playlists = data.get("playlists", {}).get("items", [])
        # Attach market so we can track it through the pipeline
        for p in playlists:
            p["_market"] = market
        return playlists

    def fetch_playlist_tracks(self, playlist_id: str) -> list[dict]:
        """Return all track items for a playlist (handles Spotify pagination)."""
        self.logger.info(f"Fetching tracks for playlist_id={playlist_id}")
        tracks, url = [], f"playlists/{playlist_id}/tracks"
        params = {"limit": 100, "fields": (
            "items(added_at,track(id,name,duration_ms,explicit,popularity,"
            "artists(id,name),album(id,name,release_date))),"
            "next"
        )}
        while True:
            page = self._get(url, params=params) if not tracks else self._paginate(url)
            items = page.get("items", [])
            tracks.extend([i for i in items if i.get("track")])   # skip null tracks
            url = page.get("next")
            if not url:
                break
            params = None   # 'next' already contains query string
        return tracks

    def _paginate(self, full_url: str) -> dict:
        """Follow a Spotify 'next' pagination URL directly."""
        resp = requests.get(full_url, headers=self._headers(), timeout=15)
        resp.raise_for_status()
        time.sleep(self.cfg.get("request_delay_seconds", 0.25))
        return resp.json()

    # ------------------------------------------------------------------ orchestrate + save
    def run(self) -> Path:
        """
        Extract all markets → all playlists → all tracks.
        Saves raw JSON to  data/raw/<YYYY-MM-DD>/.
        Returns the directory path.
        """
        run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        raw_dir = (
            Path(self.pipeline_cfg["data_dir"])
            / self.pipeline_cfg["raw_subdir"]
            / run_date
        )
        raw_dir.mkdir(parents=True, exist_ok=True)

        all_playlists, all_tracks = [], []

        for market in self.cfg["markets"]:
            playlists = self.fetch_featured_playlists(market)
            all_playlists.extend(playlists)

            for playlist in playlists:
                pid = playlist.get("id")
                if not pid:
                    continue
                tracks = self.fetch_playlist_tracks(pid)
                for t in tracks:
                    t["_playlist_id"] = pid
                    t["_market"] = market
                all_tracks.extend(tracks)

        # persist raw
        playlists_path = raw_dir / "playlists.json"
        tracks_path = raw_dir / "tracks.json"
        playlists_path.write_text(json.dumps(all_playlists, indent=2))
        tracks_path.write_text(json.dumps(all_tracks, indent=2))

        self.logger.info(
            f"Extract complete. {len(all_playlists)} playlists, "
            f"{len(all_tracks)} track items → {raw_dir}"
        )
        return raw_dir
