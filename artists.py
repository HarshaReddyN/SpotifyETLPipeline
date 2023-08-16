import featuredplaylist
import http_api 
from markets import GetMarkets
import json
import logging
import polars as pl
import gettracks_v2
import collections
import time


class GetArtists:
    def __init__(self, tracks: pl.DataFrame, batch_size):
        self.tracks = tracks
        self.batch_size = batch_size
        self.artist_detail = []
        self.data = collections.defaultdict(list)

    def fetch_artist_data(self, api):
        call_api = http_api.Api(URL=api, method='GET', logger='DEBUG', timeout=30)
        response = call_api.spotify_api()
        return json.loads(response.text)

    def get_artists_data(self):
        artist_ids_list = [artist_id for sublist in self.tracks.select('artist_id').rows() for artist_id in sublist[0].split(',')]
        flattened_artist_ids = artist_ids_list

        # Create a list of API URLs for the batch of artist IDs
        api_list = [f'https://api.spotify.com/v1/artists/{artist_id}' for artist_id in flattened_artist_ids]


        for batch_start in range(0, len(api_list), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(api_list))
            batch_apis = api_list[batch_start:batch_end]

            for api in batch_apis:
                artists_response = self.fetch_artist_data(api)
                self.artist_detail.append(artists_response)

            print(f'Processed batch {batch_start // self.batch_size + 1}')

        print(f'We received {len(self.artist_detail)} artists responses')

    def parse_artists_data(self):
        for artists in self.artist_detail:
            self.assign_data_to_dictionary(artists)
        return pl.DataFrame(self.data)

    def assign_data_to_dictionary(self, artist):
        if isinstance(artist, dict):
            artist_id = artist['id']
        if artist!= None:
            self.data['artist_id'].append(artist_id)
            self.data['artist_name'].append(artist['name'])
            self.data['artist_popularity'].append(artist['popularity'])
            self.data['followers'].append(artist['followers']['total'])
            self.data['genres'].append(artist['genres'])
        else: pass    


if __name__ == "__main__":
    print('Get Artists Started')
    start = time.perf_counter()
    # tracks_df = gettracks_v2.main()

    tracks_df = pl.DataFrame._read_csv(source=r'data/tracks.csv',has_header=True)
    print(tracks_df)
    print(f'Fetching Tracks Complete')

    tracks_df = tracks_df.head(500)


    artists_out = GetArtists(tracks=tracks_df, batch_size=100)  # Set your desired batch size here
    artists_out.get_artists_data()
    artists_output = artists_out.parse_artists_data()
    
    # Explode the nested `genres` column
    df_exploded = artists_output.explode(pl.col("genres"))

    # Rename exploded column
    # df_exploded = df_exploded.rename(columns={"genres": "genre"})

    # Reorder columns
    # df_exploded = df_exploded.select([
    #     "artist_id",
    #     'artist_name',
    #     'artist_popularity',
    #     "followers",
    #     "genre"
    # ])
    df_exploded.write_csv(file='data/artists.csv', has_header=True)
    end = time.perf_counter()
    print(f'Total Time taken to process Featured Playlists is {(end - start)}')
    print('Get Artists is Completed')
