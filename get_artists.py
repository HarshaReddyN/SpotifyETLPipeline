from http_api import Api
import json
from featuredplaylists import FeaturedPlayList
from get_tracks import GetTracks
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class GetArtists:
    
    def __init__(self, logger=None):
        self.logger = logger
        self.tracks_instance = GetTracks(logger=self.logger)

    def extract_all_artists(self):
        try:
            track_data = self.tracks_instance.extract_all_tracks()
            track_id_list = [track["track_id"] for track in track_data]
            
            all_artists = []

            for track_id in track_id_list:
                artists = self.extract_artists(track_id)
                if artists:
                    all_artists.extend(artists)

            return all_artists

        except Exception as exception:
            self.logger.error(
                f"There is an exception while working on function {self.__class__}. Here are the exception details: {str(exception)}"
            )
            raise SystemExit(str(exception)) from exception
        
    def extract_artists(self, track_id):

        url = f'https://api.spotify.com/v1/tracks/{track_id}'
        request = Api(URL=url, method='GET', logger=self.logger)
        response = request.spotify_api()

        if response is None:
            self.logger.error(f"Error accessing API for track {track_id}. Response is None.")
            return None

        artists = response.get('artists', [])
        artist_list = []

        for artist in artists:
            artist_data = {
                "artist_id": artist.get('id'),
                "artist_name": artist.get('name'),
                "artist_popularity": artist.get('popularity')
            }
            artist_list.append(artist_data)
        
        return artist_list


if __name__ == "__main__":
    artists_instance = GetArtists(logger=logger)
    artists = artists_instance.extract_all_artists()
    
    for index, artist_list in enumerate(artists, start=1):
        for artist_data in artist_list:
            artist_name = artist_data["artist_name"]
            artist_id = artist_data["artist_id"]
            artist_popularity = artist_data["artist_popularity"]
            print(f"{index}. Artist Name: {artist_name}, Artist ID: {artist_id}, Popularity: {artist_popularity}")
