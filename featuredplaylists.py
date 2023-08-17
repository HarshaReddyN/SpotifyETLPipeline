from http_api import Api
from markets import GetMarkets
import polars as pl
import collections
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class FeaturedPlayList:
    """
        This class helps us to fetch all the featured playlists based on the specific market on spotify
    """
    def __init__(self, countries:list):

        self.countries = countries
        self.featured_playlist_response = []
        self.data = collections.defaultdict(list)

    def get_featured_playlist_data(self):

        """
            This function helps us to get all featured playlists from all countries
        """

        for country in self.countries:
            logger.info(f'Fetching Playlist for Country {country}')
            url = f'https://api.spotify.com/v1/browse/featured-playlists?country={country}'
            call_api = Api(URL=url,method='GET',logger='DEBUG')
            response = call_api.spotify_api()
            self.featured_playlist_response.append(json.loads(response.text))
            logger.info(f'Fetching Playlist for Country {country} Completed, Resulted with {json.loads(response.text)["playlists"]["total"]} No of Playlists')
    
    def assign_data_to_dictionary(self, playlists):
        """
            This function helps us to assign the items to assign items to a dictionar from the features playlist response
        """
        for playlist in playlists['playlists']['items']:
            if playlist != None:
                self.data["message"].append(playlists["message"])
                self.data["playlist_name"].append(playlist['name'] if self.data['playlist_name'] != None else None)
                self.data["playlist_description"].append(playlist["description"])
                self.data["playlist_id"].append(playlist["id"])
                self.data["playlist_url"].append(playlist["external_urls"]["spotify"])
                self.data["playlist_owner"].append(playlist["owner"]["display_name"])
                self.data["track_api"].append(playlist["tracks"]["href"])
                self.data["tracks_total"].append(playlist["tracks"]["total"])
            else: None
                
    def parse_featured_playlists(self):
        for playlist in self.featured_playlist_response:
            self.assign_data_to_dictionary(playlists=playlist)
        pl.DataFrame(self.data).write_csv(file='playlist.csv',has_header=True)
        return pl.DataFrame(self.data)
def main():
    logger.info('Get Featured Playlist started')
    call_markets_instance = GetMarkets()
    markets = call_markets_instance.get_available_markets()
    call_featured_playlist = FeaturedPlayList(countries=markets)
    call_featured_playlist.get_featured_playlist_data()
    logger.info('Get Featured Playlist Completed')

    return call_featured_playlist.parse_featured_playlists()

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f'Total Time taken to process Featured Playlists is {(end-start)}')