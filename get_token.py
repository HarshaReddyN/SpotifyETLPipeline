import requests
import base64
from assets import get_assets
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

url = 'https://accounts.spotify.com/api/token'
def get_spotify_access_token(logger=None):
    try:
        credentials = f"{get_assets.CLIENT_ID.value}:{get_assets.CLIENT_SECRET.value}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
        }
        data = {
            'grant_type': 'client_credentials',
        }
        response = requests.post(url=url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()['access_token']

        else:
            logger.error(f"Failed to generate Spotify token. Status Code: {response.status_code}")
            return None
    except Exception as exception:
        logger.error(f"There is an exception while retrieving Spotify token: {str(exception)}")
        return None
