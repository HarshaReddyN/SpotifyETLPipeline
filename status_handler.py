"""
    This file helps us to handle http status codes
"""
import requests
from http_api import Api
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class Handler():
    def response_handler():
        handle = Api.spotify_api()

        elif request.status_code == 429:
            retry_after = int(request.headers.get("Retry-After", 5))
            self.logger.error(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            return self.


        elif request.status_code == 401:
            self.logger.error("Bad or expired token. This can happen if the user revoked a token or the access token has expired. You should re-authenticate the user.")
        elif request.status_code == 403:
            self.logger.error("Bad OAuth request (wrong consumer key, bad nonce, expired timestamp...). Unfortunately, re-authenticating the user won't help here.")
        elif request.status_code == 500:
            self.logger.error("The server encountered an unexpected condition that prevented it from fulfilling the request.")
