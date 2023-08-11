from http_api import Api


class Playlists:

    def __init__(self) -> None:
        pass

    def get_playlist_tracks(playlist_id):
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        request = Api(URL=url, method='GET')
        response = request.spotify_api()

        if response is None:
            print(f"Error accessing API for playlist {playlist_id}. Response is None.")
            return None

        tracks = response.get('items', [])
        return tracks

