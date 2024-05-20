import os
import pandas as pd
import numpy as np


class DataPreprocesser:
    def __init__(self, kaggle_fpath: str, eurostat_fpath: str) -> None:
        self.kaggle_fpath = kaggle_fpath
        self.eurostat_fpath = eurostat_fpath

        self.european_countries = ["Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina", "Bulgaria",
                      "Croatia", "Cyprus", "Czech Rep.", "Denmark", "Estonia", "Finland", "France", "Germany",
                      "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kosovo", "Latvia", "Liechtenstein",
                      "Lithuania", "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
                      "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Russian Federation", "San Marino",
                      "Serbia", "Slovak Rep.", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine",
                      "United Kingdom", "Vatican City"]
        
        # Not included in the kaggle data
        self.european_countries.remove("Vatican City")
        self.european_countries.remove("Turkey")
        self.european_countries.remove("Kosovo")
    


    # Function for Kaggle data preprocessing
    def __extract_values(self, df: pd.DataFrame, country: str) -> list:
        row = df[df["Country"] == country]
        vals = row.drop(["Country", "ISO2", "ISO3"], axis=1).values.flatten()
        
        # If there are no values, then fill the numpy array with nan values.
        # With problem will be solved afterwards.
        if not list(vals):
            vals = np.empty(62)
            vals[:] = np.nan

        return vals


    def _preprocess_kaggle(self) -> pd.DataFrame:
        # Loading the complete data from the world
        data = pd.read_csv(self.kaggle_fpath)

        # Selecting the European subset
        eu_names_without_comma = data["Country"].apply(lambda x: x.split(",")[0])
        eu_data = data[eu_names_without_comma.isin(self.european_countries)]
        
        # Dropping unimportant columns
        eu_data = eu_data.drop([
            "Unit", 
            "CTS_Full_Descriptor", 
            "Indicator", 
            "Source", 
            "CTS_Code",
            "CTS_Name",
            "ObjectId"
            ], axis=1)
        
        # Next step: changing representation of the dataframe for later concatenationl => flipping x- and y-axis
        climate_change_vals = { # Retrieving values from the rows
            act_country: self.__extract_values(eu_data, act_country) 
            for act_country in self.european_countries}
        
        # Build new dataframe, that contains the values in columns
        climate_change_df = pd.DataFrame()
        for country, values in climate_change_vals.items():
            temp_df = pd.DataFrame()
            temp_df["Country"] = [country] * len(values)
            temp_df["Year"] = list(range(1961, 1961 + len(values)))
            temp_df["change_degree_celcius"] = values
            climate_change_df = pd.concat([climate_change_df, temp_df])

        climate_change_df.reset_index(drop=True, inplace=True)

        # Lastly, add column with ISO_2 abbrevations for later concatentation
        iso_2_abs = eu_data["ISO2"].unique()
        subset_country_names = eu_data["Country"].unique()
        country_name_to_iso_2 = {
            country_name.split(",")[0]: iso_2_abs[idx] 
            for idx, country_name in enumerate(subset_country_names)
            }
        
        climate_change_df["ISO_2"] = climate_change_df["Country"].apply(lambda x: country_name_to_iso_2[x])
        
        # Replace GB with UK abbrevation
        climate_change_df.loc[climate_change_df["ISO_2"] == "GB" , "ISO_2"] = "UK"

        return climate_change_df

    def _preprocess_eurostat(self) -> pd.DataFrame:
        data = pd.read_csv(self.eurostat_fpath)
        data = data.drop([
            "LAST UPDATE", "DATAFLOW", "freq", "OBS_FLAG"
            ], axis=1)
        
        # Removing EU27_2020-data, since it's an average of the whole EU
        data = data[data["geo"] != "EU27_2020"]

        # Changing the abbrevation of Greece to GR
        data["geo"] = data["geo"].replace({"EL": "GR"})

        # Renaming the geo column to ISO2 and TIME_PERIOD to Year
        data = data.rename(columns={"geo": "ISO_2", "TIME_PERIOD": "Year"})        

        return data

    def get_final_data(self) -> pd.DataFrame:
        # Eurostat only covers that starting from 2000
        kaggle_data = self._preprocess_kaggle()
        kaggle_data = kaggle_data[kaggle_data["Year"] > 2000]

        # Ensure that both datasets uses the same countries
        eurostat_data = self._preprocess_eurostat()
        eurostat_data = eurostat_data[eurostat_data["ISO_2"].isin(kaggle_data["ISO_2"])]

        # The eurostat dataset contains two different values and one that we want to neglect 
        # -> build two dataframes out of it
        mtoe_data = eurostat_data[eurostat_data["unit"] == "MTOE"]
        toe_hab_data = eurostat_data[eurostat_data["unit"] == "TOE_HAB"]

        # Renaming both values accordingly
        mtoe_data = mtoe_data.rename(columns={"OBS_VALUE": "energy_million_tons_oil_equivalent"})
        toe_hab_data = toe_hab_data.rename(columns={"OBS_VALUE": "energy_million_tons_oil_equivalent"})

        # Removing the unit columns, since it's implicit in the column
        mtoe_data = mtoe_data.drop("unit", axis=1)
        toe_hab_data = toe_hab_data.drop("unit", axis=1)

        # Merging it into on big dataframe        
        final_df = toe_hab_data.merge(mtoe_data, on=["ISO_2", "Year"], how="outer")
        final_df = final_df.merge(kaggle_data, on=["ISO_2", "Year"], how="outer")

        return final_df



if __name__ == "__main__":
    root_dir = os.path.join("..", "data")
    kaggle = os.path.join(root_dir, "climate_change_indicators.csv")
    eurostat = os.path.join(root_dir, "sdg_07_10_linear.csv")

    preprocessed_data = DataPreprocesser(kaggle_fpath=kaggle, eurostat_fpath=eurostat).get_final_data()
    print(preprocessed_data.head())