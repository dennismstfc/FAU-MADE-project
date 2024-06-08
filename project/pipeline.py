import os

from downloader import DataRetriever
from preprocessing import DataPreprocesser


class DataPipeline:
    def __init__(self):
        self.ROOT_DIR = os.path.join("..", "data")
        self.kaggle = os.path.join(self.ROOT_DIR, "climate_change_indicators.csv")
        self.eurostat = os.path.join(self.ROOT_DIR, "sdg_07_10_linear.csv")

    def download_data(self):
        data_retriever = DataRetriever()
        data_retriever.download_kaggle_dataset('tarunrm09/climate-change-indicators')
    
        url = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sdg_07_10/?format=SDMX-CSV&i'
        data_retriever.download_eurostat_data(url, "sdg_07_10_linear.csv")

    def preprocess_data(self):
        return DataPreprocesser(kaggle_fpath=self.kaggle, eurostat_fpath=self.eurostat).get_final_data()

    def run(self):
        self.download_data()
        preprocessed_data = self.preprocess_data()
        print(preprocessed_data.head())
        return preprocessed_data


if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run()