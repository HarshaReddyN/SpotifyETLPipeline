from datetime import datetime
import pathlib

class Fileconvertor:
    """
    A class that handles file conversion and folder creation
    """
    def __init__(self) -> None:
        pass

    def create_folder(self, FolderName: str):
        """
        Creates a new folder inside the 'data' directory with the given name.
        @parm: Foldername has to be string

        """
        
        folder_path = pathlib.Path(f'data/{FolderName}')
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def to_csv(self, filename: str):
        """
        Converts data into a CSV file and saves it in a folder named with the current date and time.
        @parm: filename has to be string

        """

        # get current date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H-00-00")
        print("Current date & time : ", current_datetime)
        # convert datetime obj to string
        folder_name = f'{str(current_datetime)}'
        # create the folder if it doesn't exist
        folder_path = self.create_folder(FolderName=folder_name)
        # create a file object along with extension
        file_path = folder_path / f'{filename}.csv'
        try:
            with file_path.open(mode='w') as file:
                print("File created:", file_path)
            return "File Created Successfully."
        except Exception as e:
            return f"Error creating the file: {e}"
