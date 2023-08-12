import logging
import polars as pl
import collections
import time
import json
from http_api import Api
import featuredplaylists

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class GetTracks:
    def __init__(self, playlist: pl.DataFrame):
        self.playlist = playlist
        self.trackdetail = []

    def fetch_track_details(self, api_url):
        call_api = Api(URL=api_url, method='GET', logger='DEBUG')
        response = call_api.spotify_api()
        return json.loads(response.text)

    def get_tracks_data(self):
        api_list = [track[0] for track in self.playlist.select('track_api').rows()]
        for api in api_list:
            while api:
                tracks_response = self.fetch_track_details(api)
                self.trackdetail.append(tracks_response)
                api = tracks_response.get('next')

        logger.info(f'Received {len(self.trackdetail)} tracks responses')

    def parse_tracks_data(self):
        data = collections.defaultdict(list)
        for tracks in self.trackdetail:
            for track in tracks.get('items', []):
                track_info = track.get('track', {})
                data['track_added_at'].append(track.get('added_at'))
                data['track_id'].append(track_info.get('id'))
                data['track_name'].append(track_info.get('name'))

        return pl.DataFrame(data)

if __name__ == "__main__":
    logger.info('Get Tracks Started')
    start = time.perf_counter()

    playlists_df = featuredplaylists.main()
    logger.info('Fetching Playlists Complete')

    out = GetTracks(playlist=playlists_df)
    out.get_tracks_data()
    output = out.parse_tracks_data()
    output.write_csv(file='data/tracks.csv', has_header=True)

    end = time.perf_counter()
    logger.info(f'Total Time taken to process Featured Playlists is {(end - start)}')
    logger.info('Get Tracks Completed')
