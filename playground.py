import polars as pl




class Insertion:

    def insert_market():

        markets_df = pl.read_csv('Markets.csv')
        print(markets_df)