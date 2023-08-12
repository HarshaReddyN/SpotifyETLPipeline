from http_api import Api
from markets import GetMarkets
import polars as pl
import collections
import time
import json
import asyncio

class FeaturedPlayList:
    def __init__(self, countries: list):
        self.countries = countries
        self.featured_playlist_response = []
        self.data = collections.defaultdict(list)

    async def get_featured_playlist_data(self):
        call_api = Api(method='GET', logger='DEBUG')  # Reuse the API instance
        tasks = []

        async def fetch_playlist_data(country):
            url = f'https://api.spotify.com/v1/browse/featured-playlists?country={country}'
            call_api.url = url
            response = await call_api.spotify_api_async()
            self.featured_playlist_response.append(json.loads(response.text))

        for country in self.countries:
            tasks.append(fetch_playlist_data(country))

        await asyncio.gather(*tasks)

    def assign_data_to_dictionary(self, playlists):
        for playlist in playlists['playlists']['items']:
            self.data["message"].append(playlists["message"])
            self.data["playlist_name"].append(playlist["name"])
            self.data["playlist_description"].append(playlist["description"])
            self.data["playlist_id"].append(playlist["id"])
            self.data["playlist_url"].append(playlist["external_urls"]["spotify"])
            self.data["playlist_owner"].append(playlist["owner"]["display_name"])
            self.data["track_api"].append(playlist["tracks"]["href"])
            self.data["tracks_total"].append(playlist["tracks"]["total"])

    def parse_featured_playlists(self):
        for playlist in self.featured_playlist_response:
            self.assign_data_to_dictionary(playlists=playlist)
        
        pl.DataFrame(self.data).write_csv(file='playlist.csv', has_header=True)
        return pl.DataFrame(self.data)

async def main():
    print('Get Featured Playlist started')
    call_markets_instance = GetMarkets()
    markets = call_markets_instance.get_available_markets() 
    call_featured_playlist = FeaturedPlayList(countries=markets)
    await call_featured_playlist.get_featured_playlist_data()
    result = call_featured_playlist.parse_featured_playlists()
    print('Get Featured Playlist Completed')
    return result
    
if __name__ == "__main__":
    start = time.perf_counter()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main())
    end = time.perf_counter()
    print(f'Total Time taken to process Featured Playlists is {(end - start)}')
