import base64
import datetime
import logging
import json

import requests

from assets import GetAssets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

url = 'https://accounts.spotify.com/api/token'

def get_spotify_access_token(logger=None):

    """
        This function creates a token to access the Web API
    """
    try:
        credentials = f"{GetAssets.CLIENT_ID.value}:{GetAssets.CLIENT_SECRET.value}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
        }
        data = {
            'grant_type': 'client_credentials',
        }
        response = requests.post(url=url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_dict = {}
            token_dict['access_token'] = response.json()['access_token']
            token_dict['generated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            with open('api_token.json', 'w') as outfile:
                json.dump(token_dict, outfile)
            return token_dict['access_token']

        else:
            logger.error(f"Failed to generate Spotify token. Status Code: {response.status_code}")
            raise Exception
    except Exception as exception:
        logger.error(f"There is an exception while retrieving Spotify token: {str(exception)}")
        return None

