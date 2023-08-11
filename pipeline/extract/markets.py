"""
This File helps us to get all the markets available using the Spotify API
"""
from Utils.http_api import http_api
#from Utils import get_token
import os 
import sys 



print(os.getcwd())





# class Getmarkets:
#     """
#     This class contains the function that helps us to get all the markets listed on Spotify
#     """
#     def get_available_markets():
#         """
#         This Function helps us to get available markets by using the token generated on get_token Function.
#         """
#         # url = 'https://api.spotify.com/v1/browse/available-markets'
#         # headers = {'Authorization': f'Bearer {get_token()}'}
#         # response = requests.get(url, headers=headers)
        
#         # response.json().get('markets', [])
#         response = http_api.call_api(url = 'https://api.spotify.com/v1/browse/available-markets',method = 'GET')
#         print('')