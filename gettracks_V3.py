
import asyncio
import featuredplaylist
import http_api 
from markets import GetMarkets
import json
import logging
import polars as pl
import collections
import time
import aiohttp


async def get_tracks(playlist):
  apis = [track[0] for track in playlist.select('track_api').rows()]

  async with aiohttp.ClientSession() as session:
    track_tasks = []
    for api in apis:
      task = asyncio.create_task(fetch_tracks(session, api))  
      track_tasks.append(task)

    track_responses = await asyncio.gather(*track_tasks)
  
  return parse_tracks(track_responses)

async def fetch_tracks(session, api):
  async with session.get(api) as response:
    return await response.json()
  
def parse_tracks(responses):
  # parse and return dataframe 

async def main():
  playlist = featuredplaylist.main()
  
  tracks = await get_tracks(playlist)
  
  print(tracks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())