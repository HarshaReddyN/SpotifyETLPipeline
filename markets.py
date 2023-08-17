"""
This File helps us to get all the markets available using the Spotify API
"""
from http_api import Api
import json


class GetMarkets:
    
    """
    This class helps us to fetch all the available markets on spotify 
    """
    def __init__(self):
        self.url = 'https://api.spotify.com/v1/markets'
        
    def get_available_markets(self):

        """
        This Function helps us to retrieve all markets and return them in a string format
        """
        
        request = Api(URL=self.url, method='GET')
        response = request.spotify_api()
        markets = json.loads(response.text)
        out = markets['markets']
        print(out)
        return out




