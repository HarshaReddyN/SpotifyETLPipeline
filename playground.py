import psycopg2
from psycopg2 import sql
import logging
import time
import database_connection
from featuredplaylists import FeaturedPlayList
from markets import GetMarkets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


playlist = FeaturedPlayList()
data = playlist.get_featured_playlist_data()

countries = GetMarkets()

# Database connection parameters
db_params = {
    'dbname': 'spotify_etl_pipeline',
    'user': 'spotify_user',
    'password': 'HarshaG68',
    'host': 'localhost',
    'port': '5432'  # Default PostgreSQL port
}


def insert_data(data, table_name):
    start_time = time.time()
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cursor:
            columns = data.keys()
            records = zip(*data.values())

            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )

            try:
                cursor.executemany(insert_query, records)
                conn.commit()
                elapsed_time = time.time() - start_time
                logger.info(f"Inserted {cursor.rowcount} rows into {table_name} in {elapsed_time:.2f} seconds")
            except psycopg2.Error as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    table_name = 'extracted_data.featured_playlists'  # Replace with your table name
    insert_data(data, table_name)
