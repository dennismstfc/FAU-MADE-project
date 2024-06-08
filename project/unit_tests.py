import os
import pandas as pd
import unittest

from preprocessing import DataPreprocesser
from pipeline import DataPipeline


class TestDataPreprocessor(unittest.TestCase):
    '''
    test_preprocess_kaggle_data: Tests that the _preprocess_kaggle method returns a DataFrame with the correct columns.
    test_preprocess_eurostat_data: Tests that the _preprocess_eurostat method returns a DataFrame with the correct columns.
    test_get_final_data: Tests that the get_final_data method returns a DataFrame with the correct columns and no missing values.  
    (Data imputation is implictly tested here, since the function get's called in get_final_data())
    '''
    @classmethod
    def setUpClass(cls):
        # Using sample data for testing purposes, so that the data does not need to be downloaded
        SAMPLE_DIR = os.path.join("..", "sample_data")

        cls.kaggle_fpath = os.path.join(SAMPLE_DIR, "kaggle_sample.csv")
        cls.eurostat_fpath = os.path.join(SAMPLE_DIR, "eurostat_sample.csv")
        cls.preprocessor = DataPreprocesser(kaggle_fpath=cls.kaggle_fpath, eurostat_fpath=cls.eurostat_fpath)


    def test_preprocess_kaggle_data(self):
        result = self.preprocessor._preprocess_kaggle()
        self.assertIsInstance(result, pd.DataFrame)

        self.assertTrue("TIME_PERIOD" in result.columns)
        self.assertTrue("ISO2" in result.columns)
        self.assertTrue("CHANGE_INDICATOR" in result.columns)


    def test_preprocess_eurostat_data(self):
        result = self.preprocessor._preprocess_eurostat()
        self.assertIsInstance(result, pd.DataFrame)

        self.assertTrue("TIME_PERIOD" in result.columns)
        self.assertTrue("ISO2" in result.columns)
        self.assertTrue("MTOE" in result.columns)
        self.assertTrue("TOE_HAB" in result.columns)
    

    def test_get_final_data(self):
        result = self.preprocessor.get_final_data()
        self.assertIsInstance(result, pd.DataFrame)

        self.assertTrue("TIME_PERIOD" in result.columns)
        self.assertTrue("ISO2" in result.columns)
        self.assertTrue("CHANGE_INDICATOR" in result.columns)
        self.assertTrue("MTOE" in result.columns)
        self.assertTrue("TOE_HAB" in result.columns)

        # Checking data impuation
        self.assertTrue(result["CHANGE_INDICATOR"].isna().sum() == 0)
        self.assertTrue(result["MTOE"].isna().sum() == 0)
        self.assertTrue(result["TOE_HAB"].isna().sum() == 0)

        # Checking data range
        self.assertTrue(result["TIME_PERIOD"].min() >= 2000)
        self.assertTrue(result["ISO2"].str.len().max() == 2)


class TestDataPipeline(unittest.TestCase):
    '''
    setUpClass: Initializes the class variables before the tests are run.
    test_data_pipeline_run: Tests that the run method returns a DataFrame and that the final_data.csv file is created.
    '''
    @classmethod
    def setUpClass(cls):
        # Using sample data for testing purposes, so that the data does not need to be downloaded
        SAMPLE_DIR = os.path.join("..", "sample_data")
        save_path = os.path.join(SAMPLE_DIR, "final_data.csv")

        # Making sure the final data does not exist before running the tests
        if os.path.exists(save_path):
            os.remove(save_path)

        cls.pipeline = DataPipeline(save_path=save_path)

        cls.pipeline.ROOT_DIR = SAMPLE_DIR
        cls.pipeline.kaggle = os.path.join(SAMPLE_DIR, "kaggle_sample.csv")
        cls.pipeline.eurostat = os.path.join(SAMPLE_DIR, "eurostat_sample.csv")


    def test_data_pipeline_run(self):
        result = self.pipeline.run()
        self.assertIsInstance(result, pd.DataFrame)

        self.assertTrue(os.path.exists(self.pipeline.kaggle))
        self.assertTrue(os.path.exists(self.pipeline.eurostat))

        self.assertTrue(os.path.exists(self.pipeline.save_path))



if __name__ == '__main__':
    unittest.main()