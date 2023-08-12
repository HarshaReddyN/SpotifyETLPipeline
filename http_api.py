import requests
from assets import get_assets
from get_token import get_spotify_access_token
import traceback
import time
import logging
"""
# This File acts as a Module for Calling API and Fetching Response
# """

logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()

class Api():
    
    
    def __init__(self, URL: str, method: str, logger = None):
        self.URL = URL
        self.Method = method
        self.CLIENTID = get_assets.CLIENT_ID.value
        self.client_secret = get_assets.CLIENT_SECRET.value
        self.last_token_request_time = 0

        self.logger = logger

        
    def refresh_token(self):
        # current_time = time.time()
        # if current_time - self.last_token_request_time > 3600:
        #     self.access_token = get_spotify_access_token()
        #     self.last_token_request_time = current_time
        # return self.access_token
        return get_spotify_access_token()
    
    
    def spotify_api(self):
        access_token = self.refresh_token()
        self.input_variables = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}".format(token=access_token)
        }
        try:
            request = requests.request(
                self.Method,
                self.URL,
                headers=self.input_variables,
            )
            #time.sleep(0.01)

            if request.status_code == 200:
                response = request.json()
                return request
            
            elif request.status_code == 429:
                retry_after = int(request.headers.get("Retry-After", 5))
                self.logger.error (f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                return self.spotify_api() 
            
            
            elif request.status_code == 401:
                self.logger.error("Bad or expired token. This can happen if the user revoked a token or the access token has expired. You should re-authenticate the user.")
            elif request.status_code == 403:
                self.logger.error("Bad OAuth request (wrong consumer key, bad nonce, expired timestamp...). Unfortunately, re-authenticating the user won't help here.")
            elif request.status_code == 500:
                self.logger.error("The server encountered an unexpected condition that prevented it from fulfilling the request.")
        except Exception as e:
            traceback.print_exc()
            raise SystemExit(f'There is an Exception: {e}')