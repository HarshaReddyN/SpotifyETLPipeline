import featuredplaylists
import http_api
from markets import GetMarkets
import json
import logging
import polars as pl
import collections
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class GetTracks:
    def __init__(self, playlist: pl.DataFrame, batch_size=100):
        self.playlist = playlist
        self.batch_size = batch_size
        self.trackdetail = []
        self.data = collections.defaultdict(list)

    def fetch_track_data(self, api):
        call_api = http_api.Api(URL=api, method='GET', logger=logger)
        response = call_api.spotify_api()
        return json.loads(response.text)

    def get_tracks_data(self):
        api_list = [track[0] for track in self.playlist.select('track_api').rows()]
        for batch_start in range(0, len(api_list), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(api_list))
            batch_apis = api_list[batch_start:batch_end]
            for api in batch_apis:
                tracks_response = self.fetch_track_data(api)
                self.trackdetail.append(tracks_response)
                print(f'Processed batch {batch_start // self.batch_size + 1}')
            print(f'We received {len(self.trackdetail)} tracks responses')

    def parse_tracks_data(self):
        for tracks in self.trackdetail:
            self.assign_data_to_dictionary(tracks)
        return pl.DataFrame(self.data)

    def assign_data_to_dictionary(self, tracks):
        for track in tracks['items']:
            self.data["track_added_at"].append(track("added_at"))
            if track("track"):
                self.data['track_id'].append(track['track']['id'])
                self.data['track_name'].append(track['track']['name'])
                if 'artists' in track['track']:
                    artist_ids = [artist['id'] for artist in track['track']['artists']]
                    self.data['artist_id'].append(','.join(artist_ids))
                else:
                    self.data['artist_id'].append(None)
            else:
                self.data['track_id'].append(None)
                self.data['track_name'].append(None)
                self.data['artist_id'].append(None)

if __name__ == "__main__":
    print('Get Tracks Started')
    start = time.perf_counter()
    playlists_df = featuredplaylists.main()
    print(f'Fetching Playlists Complete')
    out = GetTracks(playlist=playlists_df, batch_size=100)
    out.get_tracks_data()
    output = out.parse_tracks_data()
    output.write_csv(file='data/tracks.csv', has_header=True)
    end = time.perf_counter()
    print(f'Total Time taken to process Tracks is {(end - start)}')
    print('Get Tracks is Completed')
