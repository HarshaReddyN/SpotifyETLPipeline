import json
import ssl
import requests
from assets import GetAssets
from gettoken import get_spotify_access_token
import traceback
import time
import logging
import datetime

from requests.adapters import HTTPAdapter
"""
# This File acts as a Module for Calling API and Fetching Response
# """
retry_strategy = requests.packages.urllib3.util.retry.Retry(
    total=10,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],

)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()

class Api():
    
    
    def __init__(self, URL: str, method: str, logger = None,timeout = None):
        self.URL = URL
        self.timeout = timeout
        self.Method = method
        self.CLIENTID = GetAssets.CLIENT_ID.value
        self.client_secret = GetAssets.CLIENT_SECRET.value
        self.last_token_request_time = 0

        self.logger = logger

        
    def refresh_token(self):
        with open('api_token.json','r') as token_file:
            api_token = json.load(token_file)
            token_generated_at = datetime.datetime.strptime(api_token['generated_at'], "%Y-%m-%d %H:%M:%S.%f")
            
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        if (datetime.datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S.%f')- token_generated_at).total_seconds()<3600:
            self.access_token = api_token['access_token']
        else: 
            self.access_token = get_spotify_access_token()
            
            
        return self.access_token
        return get_spotify_access_token()
    
    
    def spotify_api(self):
        access_token = self.refresh_token()
        self.input_variables = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}".format(token=access_token)
        }
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 # not use TLSv1 and TLSv1_1
            ssl_context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH') 
            if self.Method == "GET":
                response = http.get(
                    self.URL,
                    timeout= self.timeout,
                    headers=self.input_variables,
                   
                )
                #time.sleep(0.01)

            if response.status_code == 200:
                return response
            
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                self.logger.error (f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                return self.spotify_api() 
            
            
            elif response.status_code == 401:
                self.logger.error("Bad or expired token. This can happen if the user revoked a token or the access token has expired. You should re-authenticate the user.")
            elif response.status_code == 403:
                self.logger.error("Bad OAuth request (wrong consumer key, bad nonce, expired timestamp...). Unfortunately, re-authenticating the user won't help here.")
            elif response.status_code == 500:
                self.logger.error("The server encountered an unexpected condition that prevented it from fulfilling the request.")
        except Exception as e:
            traceback.print_exc()
            raise SystemExit(f'There is an Exception: {e}')