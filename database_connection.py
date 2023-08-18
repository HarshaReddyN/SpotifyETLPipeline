"""
This Module is Used to Connect to PostgreSQL Database
Class: DatabaseConnection
    Function: conncet_to_database
    Function: disconnect_from_database
"""
import base64
import logging
import sys
from pprint import pprint
import sqlalchemy
import sqlalchemy_utils
import assets
class DatabaseConnection:
    """
    Class used to connect to PostgreSQL Database and Disconnect from database
    """
    def __init__(self,) -> None:
        pass
    def conncet_to_database(self,database_host : str,port: str,user:str,password:str,database_name:str):
        """
        Function Connect to Database will be connecting to PostgreSQL
        @param: Database Host : str
        @param: Port: str
        @param: User:str
        @param: Password:base64
        @param: Database Name: str
        @RETURN: Returns Database Connection Cursor
        """
        try:
            connection_string = f'postgresql+psycopg2://{user}:{password}@{database_host}:{port}/{database_name}'
            pprint(f'Establishing Connection to Database {database_name} on host {database_host}:{port}')
            connection_engine = sqlalchemy.create_engine(connection_string)
            pprint(f'Connection Succssful to Database {database_name}')
            return connection_engine.connect()
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info() 
            self.tracebackprint(exc_type, exc_value, exc_traceback)
    def tracebackprint(self, exc_type, exc_value, exc_traceback):
        traceback_details = {
                                    'filename': exc_traceback.tb_frame.f_code.co_filename,
                                    'lineno'  : exc_traceback.tb_lineno,
                                    'name'    : exc_traceback.tb_frame.f_code.co_name,
                                    'type'    : exc_type.__name__,
                                    'message' : exc_value.msg,
                                    }
        del(exc_type, exc_value, exc_traceback)
        pprint(traceback_details)
    def disconnect_from_database(self,cursor):
        """
        @param Cursor: Database Cursor which needs to disconnected
        @RETURN: Returns Status Message of the disconnection event.
        """
        cursor.close()
        pprint(f'Connection closed Successfully')
def main():
    _ = DatabaseConnection()
    _.conncet_to_database(database_host='localhost',port='5432',user='spotify_user',password='HarshaG68',database_name='spotify_etl_pipeline')
    sql = """CREATE TABLE extracted_data.markets;"""
    #connection.execute(sql)
    print("")
if __name__ == "__main__":
    main() 