"""
This file helps us to convert the files into csv format
"""

import pandas as pd
from datetime import datetime
import pathlib


class Fileconvertor:

    """
    This Function helps us to convert the files according to requirements
    @param: filename: File name that you want to write to, Expected as string format.
    """
    def __init__(self,) -> None:
        pass
    def folder_exists(self,FolderName:str):
          return pathlib.Path(f'data/{FolderName}').is_dir()
    
    def create_folder(self,FolderName:str):
        if not Fileconvertor().folder_exists(FolderName=FolderName):
            pathlib.Path(f'data/{FolderName}').mkdir(parents=True, exist_ok= True)
            return True
        else:
            return False
            

    def to_csv(self,filename:str):
        self.filename = filename
        # get current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H-00-00")
        print("Current date & time : ", current_datetime)
        

        # convert datetime obj to string
        folder_name = f'data/{str(current_datetime)}'
        # check if folder created and create the file
        folder_created = Fileconvertor().create_folder(FolderName=folder_name)
        if folder_created:
             file_path = pathlib.Path(f'{folder_name}/{self.filename}.csv')
        else:
            return "Folder Not Created Thus, No File created"
        # create a file object along with extension
        
        with file_path.open(mode='w') as file:
            print("File created:", file_path)
        file.close()

    def tracks_to_csv():
        

    


if __name__ == "__main__":
   file = Fileconvertor()
   c = file.to_csv(filename='Markets')
