import pandas as pd
from markets import GetMarkets
from featuredplaylists import FeaturedPlayList
from converter import Fileconvertor


class main():

    def __init__(self) -> None:
        pass


    def fp_to_csv():

        df = FeaturedPlayList.parse_featured_playlists()
        convert_fp = Fileconvertor.df_to_csv(df)
