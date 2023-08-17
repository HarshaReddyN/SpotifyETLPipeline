import get_tracks
import http_api
import json
import logging
import polars as pl
import collections
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class GetArtists:
    def __init__(self, tracks_df: pl.DataFrame):
        self.tracks_df = tracks_df
        self.artist_ids = set()
        self.data = collections.defaultdict(list)

    def get_artist_details(self):
        for artist_id in self.tracks_df['artist_id']:
            if artist_id:
                self.artist_ids.update(artist_id.split(','))

        for artist_id in self.artist_ids:
            self.fetch_artist_data(artist_id)

    def fetch_artist_data(self, artist_id):
        url = f'https://api.spotify.com/v1/artists/{artist_id}'
        call_api = http_api.Api(URL=url, method='GET', logger=logger)
        response = call_api.spotify_api()
        artist_response = json.loads(response.text)
        self.data["artist_id"].append(artist_response("id"))
        self.data["artist_name"].append(artist_response("name"))
        self.data["genres"].append(','.join(artist_response("genres", [])))
        self.data["followers"].append(artist_response("followers", {})("total", 0))

if __name__ == "__main__":
    logger.info('Get Artists Started')
    start = time.perf_counter()
    tracks_df = pl.read_csv('data/tracks.csv')
    out = GetArtists(tracks_df=tracks_df)
    out.get_artist_details()
    output = pl.DataFrame(out.data)
    output.write_csv(file='data/artists.csv', has_header=True)
    end = time.perf_counter()
    logger.info(f'Total Time taken to process Artists is {(end - start)}')
    logger.info('Get Artists is Completed')
