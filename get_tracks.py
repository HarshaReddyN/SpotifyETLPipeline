from featuredplaylists import FeaturedPlayList
from http_api import Api
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class GetTracks:
    def __init__(self, logger=None):
        self.logger = logger
        self.playlist_instance = FeaturedPlayList()

    def extract_all_tracks(self):
        try:
            data = self.playlist_instance.get_featured_playlists()
            store_playlist_id = data.get("playlist_id", [])
            
            all_tracks = []

            for playlist_id in store_playlist_id:
                tracks = self.extract_tracks(playlist_id)
                if tracks:
                    all_tracks.extend(tracks)

            return all_tracks

        except Exception as exception:
            self.logger.error(
                f"There is an exception while working on function {self.__class__}. Here are the exception details: {str(exception)}"
            )
            raise SystemExit(str(exception)) from exception
        
    def extract_tracks(self, playlist_id):

        """
            This Function helps us to extract all the track info from the playlist
            @param: playlist_id ex: 'a6a98sD5DS8D7y88'
        """

        all_tracks = []
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        
        try:
            while url:
                request = Api(URL=url, method='GET', logger=self.logger)
                response = request.spotify_api()

                if response is None:
                    self.logger.error(f"Error accessing API for playlist {playlist_id}. Response is None.")
                    return None

                tracks = response.get('items', [])
                for track in tracks:
                    track_info = track.get('track')
                    if track_info:
                        track_data = {
                            "track_id": track_info.get('id'),
                            "track_name": track_info.get('name'),
                            "track_popularity": track_info.get('popularity'),
                            "artists": [artist.get('name') for artist in track_info.get('artists', [])]
                        }
                        all_tracks.append(track_data)

                url = response.get('next')
            
            return all_tracks
        
        except Exception as exception:
            self.logger.error(
                f"There is an exception while working on function {self.__class__}. Here are the exception details: {str(exception)}"
            )
            raise SystemExit(str(exception)) from exception


if __name__ == "__main__":
    tracks_instance = GetTracks(logger=logger)
    tracks = tracks_instance.extract_all_tracks()
    for index, track in enumerate(tracks, start=1):
        print(f"{index}. {track.get('track_name')}")
        print(f"   Track ID: {track['track_id']}")
        print(f"   Popularity: {track['track_popularity']}")
        print(f"   Artists: {', '.join(track['artists'])}")
        print("\n")
