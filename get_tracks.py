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
    def __init__(self,playlist:pl.DataFrame):
        self.playlist = playlist
        
        self.trackdetail = []
        self.data  = collections.defaultdict(list)

    def get_tracks_data(self):

        api_list = [track[0] for track in self.playlist.select('track_api').rows()]
        for api in api_list:
            while api:
                call_api = http_api.Api(URL=api, method='GET', logger='DEBUG')
                response = call_api.spotify_api()
                tracks_response = json.loads(response.text)
                
                self.trackdetail.append(tracks_response)
                
                if tracks_response['next']:
                    api = tracks_response['next']
                else:
                    break
            
        print(f'We received {len(self.trackdetail)} tracks responses')
    def parse_tracks_data(self):
        for tracks in self.trackdetail:
            self.assign_data_to_dictionary(tracks)
        return pl.DataFrame(self.data)

    def assign_data_to_dictionary(self, tracks):
        for track in tracks['items']:
            
            self.data["track_added_at"].append(track["added_at"])   
            self.data['track_id'].append(track['track']['id'] if track['track'] != None else None)
            self.data['track_name'].append(track['track']['name'] if track['track'] != None else None) 



        
if __name__ == "__main__":
    print('Get Tracks Started')
    start = time.perf_counter()
    playlists_df = featuredplaylists.main()
    print(f'Fetching Playlists Complete')
    out = GetTracks(playlist=playlists_df)
    out.get_tracks_data()
    output = out.parse_tracks_data()
    output.write_csv(file='data/tracks.csv',has_header=True)
    end = time.perf_counter()
    print(f'Total Time taken to process Featured Playlists is {(end-start)}')
    print('Get Tracks is  Completed')
