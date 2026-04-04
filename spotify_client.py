"""
SpotifyClient
-------------
Handles OAuth2 client-credentials token lifecycle and all API calls.

Token is fetched on first use and auto-refreshed when expired.
All GET requests are retried up to max_retries times on 429 / 5xx.
"""

import time
import base64
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str,
                 token_url: str, base_url: str,
                 max_retries: int = 3, request_delay: float = 0.3):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.base_url = base_url
        self.max_retries = max_retries
        self.request_delay = request_delay

        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def _fetch_token(self) -> None:
        """Request a fresh client-credentials token from Spotify."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        response = requests.post(
            self.token_url,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        # Subtract 30 s buffer so we refresh before actual expiry
        self._token_expiry = time.time() + data["expires_in"] - 30
        logger.info("Spotify OAuth2 token refreshed.")

    def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expiry:
            self._fetch_token()
        return self._access_token

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """
        Authenticated GET with retry logic.
        Handles 429 (rate limit) by sleeping the Retry-After header value.
        """
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, self.max_retries + 1):
            headers = {"Authorization": f"Bearer {self._ensure_token()}"}
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=10)

                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 5))
                    logger.warning("Rate limited. Sleeping %s s (attempt %s).", wait, attempt)
                    time.sleep(wait)
                    continue

                if resp.status_code in (500, 502, 503):
                    logger.warning("Server error %s on attempt %s.", resp.status_code, attempt)
                    time.sleep(2 ** attempt)
                    continue

                resp.raise_for_status()
                time.sleep(self.request_delay)
                return resp.json()

            except requests.RequestException as exc:
                logger.error("Request error on attempt %s: %s", attempt, exc)
                if attempt == self.max_retries:
                    raise

        raise RuntimeError(f"All {self.max_retries} attempts failed for {url}")

    # ------------------------------------------------------------------
    # Spotify endpoints
    # ------------------------------------------------------------------
    def get_featured_playlist(self, market: str) -> Optional[dict]:
        """
        Returns the first featured playlist object for a given market,
        or None if Spotify returns no playlists for that market.
        """
        data = self._get("/browse/featured-playlists", params={
            "country": market,
            "limit": 1,
        })
        items = data.get("playlists", {}).get("items", [])
        if not items:
            logger.warning("No featured playlist found for market %s.", market)
            return None
        return items[0]

    def get_playlist_tracks(self, playlist_id: str) -> list[dict]:
        """
        Returns all track items from a playlist, handling Spotify's
        100-item pagination automatically.
        """
        tracks = []
        endpoint = f"/playlists/{playlist_id}/tracks"
        params = {"limit": 100, "offset": 0,
                  "fields": "items(track(id,name,duration_ms,popularity,"
                            "artists(id,name),album(id,name,release_date))),"
                            "next"}

        while endpoint:
            data = self._get(endpoint, params=params)
            items = data.get("items", [])
            tracks.extend([i["track"] for i in items if i.get("track")])

            # Pagination: next is a full URL, strip base_url for _get
            next_url = data.get("next")
            if next_url:
                endpoint = next_url.replace(self.base_url, "")
                params = {}   # params are already embedded in next_url
            else:
                break

        return tracks

    def get_artist(self, artist_id: str) -> dict:
        """Returns artist metadata including genres."""
        return self._get(f"/artists/{artist_id}")
