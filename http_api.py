import datetime
import json
import logging
import ssl
import time
import traceback

import requests
from requests.adapters import HTTPAdapter

from assets import GetAssets
from get_token import get_spotify_access_token

retry_strategy = requests.packages.urllib3.util.retry.Retry(
    total=10,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class Api():
    """
    This class provides methods for calling APIs and fetching responses.
    """

    def __init__(self, URL: str, method: str, logger=None):
        """
        Initializes the API object with the API URL, method, and optional logger.

        Args:
            URL (str): The URL of the API.
            method (str): The HTTP method to use (GET, POST, etc.).
            logger (Logger, optional): Logger instance for logging. Defaults to None.
        """
        self.URL = URL
        self.Method = method
        self.CLIENTID = GetAssets.CLIENT_ID.value
        self.client_secret = GetAssets.CLIENT_SECRET.value
        self.last_token_request_time = 0
        self.logger = logger

    def refresh_token(self):
        """
            Refreshes the access token if expired.

            Returns:
                str: The refreshed access token.
        """
        with open('api_token.json', 'r') as token_file:
            api_token = json.load(token_file)
            token_generated_at = datetime.datetime.strptime(
                api_token['generated_at'], "%Y-%m-%d %H:%M:%S.%f")

        current_time = datetime.datetime.now()
        if (current_time - token_generated_at).total_seconds() < 3600:
            self.access_token = api_token['access_token']
        else:
            return get_spotify_access_token()

    def spotify_api(self):
        """
            Makes the API request and handles various HTTP responses.

            Returns:
                Response: The response object.
        """
        access_token = self.refresh_token()
        self.input_variables = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}".format(token=access_token)
        }
        try:
            response = http.request(
                self.Method,
                self.URL,
                headers=self.input_variables,
            )

            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                self.logger.error(
                    f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                return self.spotify_api()
            elif response.status_code == 401:
                self.logger.error(
                    "Bad or expired token. Re-authenticate the user.")
            elif response.status_code == 403:
                self.logger.error(
                    "Bad OAuth request. Re-authenticating won't help here.")
            elif response.status_code == 500:
                self.logger.error(
                    "Server encountered an unexpected condition.")
        except Exception as e:
            traceback.print_exc()
            raise SystemExit(f'There is an Exception: {e}')
