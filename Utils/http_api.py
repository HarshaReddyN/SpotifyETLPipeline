"""
This File acts as a Module for Calling API and Fetching Response
"""
import requests
import json
from Utils import get_assets


class http_api():
    """
    This Class is Used to Fetch The Response from API

    """
    def __init__(self,URL:str,Method:str):
        """
        This Function is Used to Call the Provided API with Provided Method and return the Response of the API
        @Param: URL : URL to call and get response from EX: (http://test.com)
        @param: Method : Method to call the API with Ex: (GET, POST, PATCH, UPDATE)
        @Output: Response as --> JSON 
        """
        self.URL = ''
        self.Method = ''
        self.client_id = ''
        self.client_secret = ''
        self.input_variables = {
        "Accept" : "application/json",
        "Content-Type" : "application/json",
        "Authorization" : "Bearer {token}".format(token='')
    }
    def call_api(self):
        """
        This Function is Used to Call the Provided API with Provided Method and return the Response of the API
        @Output: Response as --> JSON 
         """
        try:
            request = requests.self.Method(

                self.URL,headers = self.input_variables,
            )
            response = request.json()
            return response
        except Exception as VE:
            raise SystemExit(f'There is a Exception raised while calling API, Proabable casue is some Value Error, For Detailed Information. please refer to Exception Details : {str(VE)}')
        