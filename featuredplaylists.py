import collections
import json
import logging
import time

import polars as pl

from http_api import Api
from markets import GetMarkets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class FeaturedPlayList:
    """
    This class fetches featured playlists from Spotify based on specific markets.
    """
    def __init__(self, countries:list):
        """
        Initializes the FeaturedPlayList object with a list of countries.

        Args:
            countries (list): List of country codes to fetch featured playlists for.
        """
        self.countries = countries
        self.featured_playlist_response = []
        self.data = collections.defaultdict(list)

    def get_featured_playlist_data(self):
        """
        Fetches featured playlists for each country and stores the data.

        Returns:
            None
        """
        try:
            for country in self.countries:
                logger.info(f'Fetching Playlist for Country {country}')
                url = f'https://api.spotify.com/v1/browse/featured-playlists?country={country}'
                call_api = Api(URL=url, method='GET', logger='DEBUG')
                response = call_api.spotify_api()
                self.featured_playlist_response.append(json.loads(response.text))
                logger.info(f'Fetching Playlist for Country {country} Completed, Resulted with {json.loads(response.text)["playlists"]["total"]} No of Playlists')
        except Exception as e:
            logger.error(f'Error while fetching playlists: {e}')

    def assign_data_to_dictionary(self, playlists):
        """
        Assigns playlist data to a dictionary.

        Args:
            playlists (dict): Playlist data from the API response.

        Returns:
            None
        """
        for playlist in playlists['playlists']['items']:
            if playlist:
                self.data["message"].append(playlists["message"])
                self.data["playlist_name"].append(playlist['name'])
                self.data["playlist_description"].append(playlist["description"])
                self.data["playlist_id"].append(playlist["id"])
                self.data["playlist_url"].append(playlist["external_urls"]["spotify"])
                self.data["playlist_owner"].append(playlist["owner"]["display_name"])
                self.data["track_api"].append(playlist["tracks"]["href"])
                self.data["tracks_total"].append(playlist["tracks"]["total"])

    def parse_featured_playlists(self):
        """
        Parses the fetched featured playlist data and returns a DataFrame.

        Returns:
            polars.DataFrame: DataFrame containing parsed playlist data.
        """
        try:
            for playlist in self.featured_playlist_response:
                self.assign_data_to_dictionary(playlists=playlist)
            df = pl.DataFrame(self.data)
            df.write_csv(file='playlist.csv', has_header=True)
            return df
        except Exception as e:
            logger.error(f'Error while parsing playlists: {e}')
            return None

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
    logger.info(f'Total Time taken to process Featured Playlists is {(end-start):.2f} seconds')
