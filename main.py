from http_api import Api
import logging
import time
import collections
import polars as pl
from featuredplaylist import FeaturedPlayList  
from gettracks import GetTracks  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def main():
    call_playlist_instance = FeaturedPlayList(countries=[], logger=logger)
    playlist_data = call_playlist_instance.get_featured_playlists()

    if playlist_data is not None and "playlist_id" in playlist_data.columns:
        for playlist_id in playlist_data["playlist_id"]:
            tracks_instance = GetTracks(playlist_id=playlist_id, logger=logger)
            tracks_instance.get_tracks_from_playlist()
    else:
        logger.warning("No valid playlist data found.")


if __name__ == "__main__":
    start = time.perf_counter()
    print('Get Tracks from Playlist started')
    main()
    end = time.perf_counter()
    print(f'Total Time taken to process tracks from playlist is {(end-start)}')
    print('Get Tracks from Playlist Completed')
