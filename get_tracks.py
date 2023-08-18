import collections
import json
import logging
import time

import polars as pl

import featuredplaylists
import http_api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class GetTracks:
    """
    A class to fetch and process track data from Spotify APIs based on provided playlists.
    """

    def __init__(self, playlist: pl.DataFrame, batch_size=100):
        """
        Initialize the GetTracks instance.

        :param playlist: A DataFrame containing playlist data.
        :param batch_size: Batch size for fetching tracks data.
        """
        self.playlist = playlist
        self.batch_size = batch_size
        self.trackdetail = []
        self.data = collections.defaultdict(list)

    def fetch_track_data(self, api):
        """
        Fetch track data from the provided API.

        @param api: The API endpoint for fetching track data.
        @return: The fetched track data in JSON format.
        """
        call_api = http_api.Api(URL=api, method='GET', logger=logger)
        response = call_api.spotify_api()
        return json.loads(response.text)

    def get_tracks_data(self):
        """
        Fetch track data for the provided playlists and store in `trackdetail`.
        """
        try:
            api_list = [track[0] for track in self.playlist.select('track_api').rows()]
            for batch_start in range(0, len(api_list), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(api_list))
                batch_apis = api_list[batch_start:batch_end]
                for api in batch_apis:
                    try:
                        tracks_response = self.fetch_track_data(api)
                        self.trackdetail.append(tracks_response)
                        logger.info(f'Processed batch {batch_start // self.batch_size + 1}')
                    except Exception as e:
                        logger.error(f'Error processing API {api}: {str(e)}')
                logger.info(f'We received {len(self.trackdetail)} tracks responses')
        except Exception as e:
            logger.error(f'An error occurred: {str(e)}')


    def parse_tracks_data(self):
        """
        Parse the fetched track data and store it in a DataFrame.
        @return: A DataFrame containing parsed track data.
        """
        for tracks in self.trackdetail:
            self.assign_data_to_dictionary(tracks)
        return pl.DataFrame(self.data)

    def assign_data_to_dictionary(self, tracks):
        """
        Assign relevant track data to the dictionary.

        @param tracks: The fetched track data in JSON format.
        """
        for track in tracks['items']:
            self.data["track_added_at"].append(track.get("added_at", None))
            if track.get("track"):
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
    try:
        logger.info('Get Tracks Started')
        start = time.perf_counter()
        playlists_df = featuredplaylists.main()
        logger.info(f'Fetching Playlists Complete')
        out = GetTracks(playlist=playlists_df, batch_size=100)
        out.get_tracks_data()
        output = out.parse_tracks_data()
        output.write_csv(file='data/tracks.csv', has_header=True)
        end = time.perf_counter()
        logger.info(f'Total Time taken to process Tracks is {(end - start)}')
        logger.info('Get Tracks is Completed')
    except Exception as e:
        logger.error(f'An error occurred: {str(e)}')
