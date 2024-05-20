import os

from downloader import DataRetriever
from preprocessing import DataPreprocesser

ROOT_DIR = os.path.join("..", "data")

if __name__ == "__main__":
    # Download part
    data_retriever = DataRetriever()
    data_retriever.download_kaggle_dataset('tarunrm09/climate-change-indicators')
    
    url = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sdg_07_10/?format=SDMX-CSV&i'
    data_retriever.download_eurostat_data(url, "sdg_07_10_linear.csv")

    # Preprocessing part
    kaggle = os.path.join(ROOT_DIR, "climate_change_indicators.csv")
    eurostat = os.path.join(ROOT_DIR, "sdg_07_10_linear.csv")

    preprocessed_data = DataPreprocesser(kaggle_fpath=kaggle, eurostat_fpath=eurostat).get_final_data()
    print(preprocessed_data.head())

    final_data_path = os.path.join(ROOT_DIR, "final_data.csv")
    preprocessed_data.to_csv(final_data_path)