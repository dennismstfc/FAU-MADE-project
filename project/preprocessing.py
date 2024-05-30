import pandas as pd
import numpy as np


class DataPreprocesser:
    def __init__(self, kaggle_fpath: str, eurostat_fpath: str) -> None:
        self.kaggle_fpath = kaggle_fpath
        self.eurostat_fpath = eurostat_fpath

        self.code_mapping = {
            'AL': 'AL', 'AT': 'AT', 'BA': 'BA', 'BE': 'BE', 'BG': 'BG', 'CY': 'CY', 'CZ': 'CZ',
            'DE': 'DE', 'DK': 'DK', 'EE': 'EE', 'EL': 'GR', 'ES': 'ES', 'FI': 'FI', 'FR': 'FR',
            'HR': 'HR', 'HU': 'HU', 'IE': 'IE', 'IS': 'IS', 'IT': 'IT', 'LT': 'LT', 'LU': 'LU',
            'LV': 'LV', 'ME': 'ME', 'MK': 'MK', 'MT': 'MT', 'NL': 'NL', 'NO': 'NO', 'PL': 'PL',
            'PT': 'PT', 'RO': 'RO', 'RS': 'RS', 'SE': 'SE', 'SI': 'SI', 'SK': 'SK', 'TR': 'TR',
            'UK': 'GB', 'XK': 'XK', 'EU27_2020': 'EU'
        }

        self.european_countries_iso2 = list(self.code_mapping.values())
    

    def convert_to_iso2(self, code: str) -> str:
        if code in self.code_mapping:
            return self.code_mapping[code]
        else:
            raise Exception(f"Unknown code: {code}")

    
    def _preprocess_eurostat(self) -> pd.DataFrame:
        data = pd.read_csv(self.eurostat_fpath)
        
        '''
        Creating for MTOE and TOE_HAB units two distinct dataframes. 
        I found in the data exploration that some years are missing, therefore pivot_table is used.
        This function creates a dataframe with the years as index and the countries as columns.
        Missing values are filled with NaN, which will be interpolated afterwards.
        '''
        mtoe_df = data[data["unit"] == "MTOE"].pivot_table(index="TIME_PERIOD", columns="geo", values="OBS_VALUE")
        mtoe_df.reset_index(inplace=True)

        # Transforming the columns to row for later concatenation.
        mtoe_df = mtoe_df.melt(id_vars="TIME_PERIOD", var_name="geo", value_name="MTOE")

        # Doing the same for the TOE_HAB data
        toe_hab_df = data[data["unit"] == "TOE_HAB"].pivot_table(index="TIME_PERIOD", columns="geo", values="OBS_VALUE")
        toe_hab_df.reset_index(inplace=True)
        toe_hab_df = toe_hab_df.melt(id_vars="TIME_PERIOD", var_name="geo", value_name="TOE_HAB")

        # Merge both dataframes into one
        processed_df = mtoe_df.merge(toe_hab_df, on=["TIME_PERIOD", "geo"])
        
        # Lastly, convert the country codes to ISO_2
        processed_df["ISO2"] = processed_df["geo"].apply(lambda x: self.convert_to_iso2(x))    

        return processed_df.drop("geo", axis=1)


    def _preprocess_kaggle(self) -> pd.DataFrame:
        # Loading the complete data from the world
        data = pd.read_csv(self.kaggle_fpath)

        # Creating a dictionary that maps the ISO2 abbrevation to the country name. Will be used for later for enriching the data.
        self.iso2_to_country = {
            data["ISO2"].to_list()[idx]: data["Country"].to_list()[idx] for idx in range(len(data))
            }

        data = data.drop([
            "ObjectId", 
            "Country", 
            "ISO3", 
            "Indicator", 
            "Unit", 
            "Source", 
            "CTS_Code", 
            "CTS_Name",
            "CTS_Full_Descriptor"], axis=1)

        # Get the correct years by removing the F in the columns
        data.columns = [el.replace("F", "") for el in data.columns]

        '''
        This preprocessing step should be done in a similar way as for the Eurostat data.
        Therefore the data will get transposed, so that the ISO2 abbrevations are the column names
        Afterwards, the data will get transformed similarly to the Eurostat data.
        ISO2 gets renamed to TIME_PERIOD, since the years are saved there after the transpose.
        '''
        data.rename(columns={"ISO2": "TIME_PERIOD"}, inplace=True)
        data.set_index("TIME_PERIOD", inplace=True)
        transposed_data = data.T
        transposed_data.reset_index(inplace=True)

        # Renaming the index column as TIME_PERIOD, since the years are saved there
        transposed_data.rename(columns={"index": "TIME_PERIOD"}, inplace=True)

        # Transforming columns to rows, similary as in _preprocess_eurostat()
        processed_data = transposed_data.melt(id_vars="TIME_PERIOD", var_name="ISO2", value_name="CHANGE_INDICATOR")
        processed_data["TIME_PERIOD"] = processed_data["TIME_PERIOD"].astype(int)

        # Selecting only the european countries
        return processed_data[processed_data["ISO2"].isin(self.european_countries_iso2)]


    def clean_and_interpolate_data(self, df: pd.DataFrame, col: str, max_missing: int = 10) -> pd.DataFrame:
        # Count missing values for each country and identify countries to remove
        missing_counts = df[df[col].isnull()]["ISO2"].value_counts()
        to_remove = missing_counts[missing_counts > max_missing].index.tolist()

        print("Removing countries with more than 10 missing values for column: ", col, to_remove)
        
        # Remove countries with more than max_missing missing values
        df_cleaned = df[~df["ISO2"].isin(to_remove)].copy()
        
        # Interpolate missing values for the specified column in the remaining countries
        df_cleaned[col] = df_cleaned.groupby("ISO2")[col].transform(lambda group: group.interpolate())
        
        # Removing column when interpolation is not possible due to missing values at the beginning
        missing_values = df_cleaned[df_cleaned[col].isnull()]["ISO2"].value_counts().index.tolist()
        df_cleaned = df_cleaned[~df_cleaned["ISO2"].isin(missing_values)]

        print("Countries removed due to missing values at beginning (intperolation fails): ", missing_values)

        return df_cleaned.reset_index(drop=True)


    def get_final_data(self) -> pd.DataFrame:
        # Ensure that both datasets uses the same countries
        eurostat_data = self._preprocess_eurostat()

        # Eurostat only covers that starting from 2000
        kaggle_data = self._preprocess_kaggle()

        kaggle_data = kaggle_data[kaggle_data["TIME_PERIOD"] >= eurostat_data["TIME_PERIOD"].min()]

        # Depending which dataset covers more countries, we will use the subset of the other dataset
        kaggle_countries = kaggle_data["ISO2"].unique()
        eurostat_countries = eurostat_data["ISO2"].unique()

        # Select the countries that are in both datasets
        common_countries = list(set(kaggle_countries) & set(eurostat_countries)) 
        print("Common countries: ", common_countries)

        # Filter the dataframes to only include the common countries
        kaggle_data = kaggle_data[kaggle_data["ISO2"].isin(common_countries)]
        eurostat_data = eurostat_data[eurostat_data["ISO2"].isin(common_countries)]
        print("Countries not included in the final dataset: ", set(kaggle_countries) ^ set(eurostat_countries))

        final_df = pd.merge(kaggle_data, eurostat_data, on=["ISO2", "TIME_PERIOD"], how="inner")

        print("Missing values in the final dataset before interpolation in percentage: ", final_df.isna().sum() / final_df.size)
        print("Final data description before interpolation: ", final_df.describe())

        print("\n -----------------------------------")
        print("Performing interpolation for the final dataset.")
        print("-----------------------------------\n")

        final_df = self.clean_and_interpolate_data(df=final_df, col="MTOE")
        final_df = self.clean_and_interpolate_data(df=final_df, col="TOE_HAB")    
        final_df = self.clean_and_interpolate_data(df=final_df, col="CHANGE_INDICATOR")

        print("Missing values in the final dataset after interpolation in percentage: ", final_df.isna().sum() / final_df.size)
        print("Final data description after interpolation: ", final_df.describe())

        print("Final dataset shape: ", final_df.shape)
        print("Final dataset columns: ", final_df.columns)
        print("Final dataset countries: ", final_df["ISO2"].unique())

        return final_df