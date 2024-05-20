import os
from kaggle.api.kaggle_api_extended import KaggleApi
import requests


class DataRetriever:
    def __init__(self) -> None:
        self.ROOT_DIR = os.path.join("..", "data")

    # Downloads a Kaggle dataset given its name. Make sure that API key is provided.
    def download_kaggle_dataset(self, dataset_name: str) -> None:
        # Init API 
        api = KaggleApi()
        api.authenticate()
        
        # Download data
        api.dataset_download_files(dataset_name, path=self.ROOT_DIR, unzip=True)

    # Downloads data from the Eurostat API.  
    def download_eurostat_data(self, url: str, dataset_name: str ='eurostat_data.csv') -> None:
        fpath = os.path.join(self.ROOT_DIR, dataset_name)        

        print(f"Downloading: {url}")

        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Check that the request was successful

        # Write the content of the response to the given path
        with open(fpath, 'wb') as file:
            file.write(response.content)

        print(f"Data has been saved to {fpath}")