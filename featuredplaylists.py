from http_api import Api
from markets import GetMarkets
import polars as pl
import collections
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class FeaturedPlayList:

    """
        This class helps us to fetch all the featured playlists based on the specific market on spotify 

    """

    def __init__(self, logger=None):
        self.logger = logger
        call_markets_instance = GetMarkets()
        self.markets = call_markets_instance.get_available_markets()

    def get_featured_playlists(self):

        """
            This Function helps us to retrieve featured playlists from the market

        """

        data = collections.defaultdict(list)

        for country_code in self.markets:
            url = f'https://api.spotify.com/v1/browse/featured-playlists?country={country_code}'
            request = Api(URL=url, method='GET', logger=self.logger)
            response = request.spotify_api()

            if response is None:
                self.logger.error(f"Error accessing API for market {country_code}. Response is None.")
                

            self.assign_data_to_dictionary(data, response, country_code)

        return data

    def assign_data_to_dictionary(self, data, response, country_code):

        """
            This function helps us to assign the items to assign items to a dictionar from the features playlist response

        """

        playlists = response.get('playlists', {}).get('items', [])

        for playlist in playlists:
            data["message"].append(response.get("message"))
            data["country_code"].append(country_code)
            data["playlist_name"].append(playlist.get("name"))
            data["playlist_description"].append(playlist.get("description"))
            data["playlist_id"].append(playlist.get("id"))
            data["playlist_url"].append(playlist.get("external_urls", {}).get("spotify"))
            data["playlist_owner"].append(playlist.get("owner", {}).get("display_name"))
            data["playlist_tracks"].append(playlist.get("tracks", {}).get("total"))

    def parse_featured_playlists(self):

        """
            This funciton helps us to parse the data into a dataframe
        """

        try:
            data = self.get_featured_playlists()  # Call the method to get data
            return pl.DataFrame(data)
        except Exception as exception:
            self.logger.error(
                f"There is an exception while working on function {self.__class__}. Here are the exception details: {str(exception)}"
            )
            raise SystemExit(str(exception))

if __name__ == "__main__":
    feature_instance = FeaturedPlayList(logger=logger)
    fp = feature_instance.parse_featured_playlists()
    print(fp)
