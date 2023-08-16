import featuredplaylist
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
    def __init__(self, playlist: pl.DataFrame, batch_size=10):
        self.playlist = playlist
        self.batch_size = batch_size
        self.trackdetail = []
        self.data = collections.defaultdict(list)

    def fetch_track_data(self, api):
        call_api = http_api.Api(URL=api, method='GET', logger='DEBUG',timeout = 30)
        response = call_api.spotify_api()
        return json.loads(response.text)

    def get_tracks_data(self):
        api_list = [track[0] for track in self.playlist.select('track_api').rows()]

        for batch_start in range(0, len(api_list), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(api_list))
            batch_apis = api_list[batch_start:batch_end]
            print(f'A Batch with {len(api_list)} is being pushed for execution')

            for api in batch_apis:
                tracks_response = self.fetch_track_data(api)
                self.trackdetail.append(tracks_response)

            print(f'Processed batch {batch_start // self.batch_size + 1}')

        print(f'We received {len(self.trackdetail)} playlists responses')

    def parse_tracks_data(self):
        for tracks in self.trackdetail:
            self.assign_data_to_dictionary(tracks)
        pl.DataFrame(self.data).write_csv(file='data/tracks.csv',has_header=True)
        return pl.DataFrame(self.data)

    def assign_data_to_dictionary(self, tracks):
        for track in tracks['items']:
            if track['track']!=None:
                self.data["track_added_at"].append(track["added_at"])
                self.data['track_id'].append(track['track']['id'] if track['track'] else None)
                self.data['track_name'].append(track['track']['name'] if track['track'] else None)          
                artist_ids = [artist['id'] for artist in track['track']['artists']]
                self.data['artist_id'].append(','.join(artist_ids) if artist_ids else None)
            else: pass  

            
            # artists = track['track']['artists'] if track['track'] else []
            # artist_ids = [artist['id'] for artist in artists]
            # self.data['artist_ids'].append(artist_ids)

    # Ensure equal lengths for all columns in case some tracks have fewer artists
        # max_artists = max(len(ids) for ids in self.data['artist_ids'])
        # for i in range(len(self.data['artist_ids'])):
        #     self.data['artist_ids'][i] += [None] * (max_artists - len(self.data['artist_ids'][i]))
            

def main():
    playlists_df = featuredplaylist.main()
    print(f'Fetching Playlists Complete')

    playlists_df = playlists_df.head(100)


    out = GetTracks(playlist=playlists_df, batch_size=100)  # Set your desired batch size here
    out.get_tracks_data()
    output = out.parse_tracks_data()
    return output

if __name__ == "__main__":
    print('Get Tracks Started')
    start = time.perf_counter()
    main()
    end = time.perf_counter()

    print(f'Total Time taken to process Tracks is {(end - start)}')
    print('Get Tracks is Completed')
