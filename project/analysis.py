import os 
import pandas as pd
import geopandas as gpd
import pandas as pd

import os
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Polygon

from typing import Tuple

ROOT_DIR = os.path.join("..", "data")


class Analysis:
    def __init__(self, data: pd.DataFrame) -> None:
        iso2_to_iso3_europe = {
            "AL": "ALB", "AD": "AND", "AT": "AUT", "BY": "BLR", 
            "BE": "BEL", "BA": "BIH", "BG": "BGR", "HR": "HRV",  
            "CY": "CYP", "CZ": "CZE", "DK": "DNK", "EE": "EST",  
            "FO": "FRO", "FI": "FIN", "FR": "FRA", "DE": "DEU", 
            "GI": "GIB", "GR": "GRC", "GG": "GGY", "HU": "HUN", 
            "IS": "ISL", "IE": "IRL", "IM": "IMN", "IT": "ITA",  
            "JE": "JEY", "LV": "LVA", "LI": "LIE", "LT": "LTU",  
            "LU": "LUX", "MT": "MLT", "MD": "MDA", "MC": "MCO",  
            "ME": "MNE", "NL": "NLD", "MK": "MKD", "NO": "NOR",
            "PL": "POL", "PT": "PRT", "RO": "ROU", "RU": "RUS",
            "SM": "SMR", "RS": "SRB", "SK": "SVK", "SI": "SVN",
            "ES": "ESP", "SJ": "SJM", "SE": "SWE", "CH": "CHE",
            "UA": "UKR", "GB": "GBR", "VA": "VAT",
        }
        
        data["ISO3"] = data["ISO2"].map(iso2_to_iso3_europe)
        self.data = data
    
        self.__enrich_data_with_geopandas()
        self.PLOT_ROOT_DIR = os.path.join("..", "plots")
        self.__create_plot_folder()

        self.column_name_to_title_description = {
            "CHANGE_INDICATOR": "Temperature change indicator (degrees Celsius)",
            "TOE_HAB": "Tonnes of Oil Equivalents per capita",
            "MTOE": "Total Million Tonnes of Oil Equivalent per year",
        }


    def __create_plot_folder(self) -> None:
        if not os.path.exists(self.PLOT_ROOT_DIR):
            os.makedirs(self.PLOT_ROOT_DIR)

    def __enrich_data_with_geopandas(self) -> gpd.GeoDataFrame:
        # Load the world map
        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        europe = world[world["continent"] == "Europe"]

        # Removing French Guina from the map due to visualization issues
        tmp = [x.replace(')','') for x in str(europe.loc[43,'geometry']).split('((')[1:]][1]
        tmp2 = [x.split(' ') for x in tmp.split(', ')][:-1]
        tmp3 = [(float(x[0]),float(x[1])) for x in tmp2]
        france_mainland = Polygon(tmp3)
        europe.loc[europe['name']=='France','geometry'] = france_mainland 

        # Select the countries that are data included
        europe = europe.copy()
        europe.loc[:, "in_final_data"] = europe["iso_a3"].isin(self.data["ISO3"])
        europe = europe[europe["in_final_data"]]
        europe = europe.reset_index()

        # Append the content of the data to the geopandas dataframe
        europe = europe.merge(self.data, left_on="iso_a3", right_on="ISO3")

        # Removing unnecessary columns
        europe = europe.drop([
            "index", 
            "in_final_data", 
            "pop_est",
            "continent",
            "iso_a3",
            "COUNTRY",
            "ISO2",
            "ISO3",
            "gdp_md_est"
            ], axis=1)
        
        europe = europe.rename(columns={
            "name": "COUNTRY"
        })

        self.europe = europe
    
    def create_map_plot(
            self, 
            column: str, 
            average: bool = True
            ) -> None:

        if column not in self.europe.columns:
            raise ValueError(f"Column {column} not in the dataframe")        

        fig, ax = plt.subplots(1, 1, figsize=(20, 10)) 

        if average:
            average_data = self.europe.groupby("COUNTRY")[column].mean().reset_index()
            europe_avg =self.europe.drop_duplicates("COUNTRY").merge(
                average_data, on="COUNTRY", suffixes=("", "_avg"))

            europe_avg.boundary.plot(ax=ax, color="black")
            europe_avg.plot(column=column+"_avg", ax=ax, legend=True, cmap="Reds")
            plt.title("Average " + self.column_name_to_title_description[column])
        else:
            self.europe.boundary.plot(ax=ax, color="black")
            self.europe.plot(column=column, ax=ax, legend=True, cmap="Reds")
            plt.title(self.column_name_to_title_description[column])
        
        # Removing numbers from the axis
        plt.xticks([])
        plt.yticks([])

        plt.tight_layout()
        
        save_path = os.path.join(self.PLOT_ROOT_DIR, column + "_map.png")
        plt.savefig(save_path)
        plt.show()

    def create_heatmap(
            self, 
            column: str, 
            cmap: str
            ) -> None:

        if column not in self.europe.columns:
            raise ValueError(f"Column {column} not in the dataframe")

        pivot_table = self.europe.pivot(index="COUNTRY", columns="TIME_PERIOD", values=column)

        plt.figure(figsize=(20, 10))
        sns.heatmap(pivot_table, annot=True, cmap=cmap, fmt=".2f")
        plt.title(f"{self.column_name_to_title_description[column]} over the years for each country")    
        plt.ylabel("Country")
        plt.xlabel("Year")

        save_path = os.path.join(self.PLOT_ROOT_DIR, column + "_heatmap.png")
        plt.savefig(save_path)
        plt.tight_layout()  
        plt.show()
        
    def create_lineplot(
            self, 
            column: str,
            average: bool = True,
            confidence_interval: bool = False,
            ylim: Tuple[int, int] = None,
            xlim: Tuple[int, int] = None
            ) -> None:

        if column not in self.europe.columns:
            raise ValueError(f"Column {column} not in the dataframe")
        
        if average:
            average_data = self.europe.groupby("TIME_PERIOD")[column].mean().reset_index()
            europe_avg = self.europe.drop_duplicates("TIME_PERIOD").merge(
                average_data, on="TIME_PERIOD", suffixes=("", "_avg"))

            sns.lineplot(data=europe_avg, x="TIME_PERIOD", y=column+"_avg")
            plt.title("Average " + self.column_name_to_title_description[column])
        
            if confidence_interval:
                ci_per_year = self.europe.groupby("TIME_PERIOD")[column].agg(["std", "size"]).reset_index()

                # Calculating by default a 95% confidence interval. TODO: Make it a parameter
                ci_per_year["ci"] = 1.96 * ci_per_year["std"] / ci_per_year["size"]**0.5

                plt.fill_between(
                    ci_per_year["TIME_PERIOD"], 
                    europe_avg[column+"_avg"] - ci_per_year["ci"], 
                    europe_avg[column+"_avg"] + ci_per_year["ci"], 
                    alpha=0.3, label="95% confidence interval"
                )

        else:
            self.europe.plot(x="TIME_PERIOD", y=column, legend=False)
            plt.title(self.column_name_to_title_description[column])

        if ylim:
            plt.ylim(ylim)
        if xlim:
            plt.xlim(xlim)

        if column == "CHANGE_INDICATOR":
            plt.ylabel("Temperature change in degrees Celsius")
        else:
            plt.ylabel(column)

        plt.xlabel("Year")
        plt.grid(True)
        plt.legend()

        save_path = os.path.join(self.PLOT_ROOT_DIR, column + "_lineplot.png")
        plt.savefig(save_path)

        plt.show()

    def create_scatterplot(
            self,
            column_x: str, 
            column_y: str, 
            average: bool = False) -> None:
        
        if column_x not in self.europe.columns:
            raise ValueError(f"Column {column_x} not in the dataframe")
        if column_y not in self.europe.columns:
            raise ValueError(f"Column {column_y} not in the dataframe")
        
        if average:
            average_data = self.europe.groupby("COUNTRY")[column_x].mean().reset_index()
            europe_avg = self.europe.drop_duplicates("COUNTRY").merge(
                average_data, on="COUNTRY", suffixes=("", "_avg"))

            sns.scatterplot(data=europe_avg, x=column_x+"_avg", y=column_y)
            plt.title(f"Average {self.column_name_to_title_description[column_x]} vs {self.column_name_to_title_description[column_y]}")

        else:
            sns.scatterplot(data=self.europe, x=column_x, y=column_y)
            plt.title(f"{self.column_name_to_title_description[column_x]} vs {self.column_name_to_title_description[column_y]}")

        plt.xlabel(self.column_name_to_title_description[column_x])
        plt.ylabel(self.column_name_to_title_description[column_y])

        save_path = os.path.join(self.PLOT_ROOT_DIR, column_x + "_" + column_y + "_scatterplot.png")
        plt.savefig(save_path)

        plt.show()

    def create_correlation_plot(self) -> None:
        plt.figure(figsize=(12, 10))
        
        tmp_europe = self.europe.drop(
            ["TIME_PERIOD", "geometry", "COUNTRY"], axis=1)

        sns.heatmap(tmp_europe.corr(), annot=True, cmap="coolwarm")
        
        save_path = os.path.join(self.PLOT_ROOT_DIR, "correlation_plot.png")
        plt.savefig(save_path)
        plt.show()


if __name__ == "__main__":
    data_path = os.path.join(ROOT_DIR, "final_data.csv")
    
    data = pd.read_csv(data_path)

    analysis = Analysis(data)
    analysis.create_map_plot("CHANGE_INDICATOR", average=True)

    analysis.create_heatmap("CHANGE_INDICATOR", cmap="Reds")
    analysis.create_heatmap("TOE_HAB", cmap="coolwarm")
    analysis.create_heatmap("MTOE", cmap="coolwarm")

    analysis.create_lineplot("CHANGE_INDICATOR", average=True, confidence_interval=True)
    
    analysis.create_lineplot(
        "TOE_HAB", 
        average=True, 
        confidence_interval=True,
        ylim=(1, 6)
        )

    analysis.create_lineplot(
        "MTOE", 
        average=True, 
        confidence_interval=True,
        ylim=(0, 100)
        )
    
    analysis.create_scatterplot("CHANGE_INDICATOR", "TOE_HAB", average=True)
    analysis.create_scatterplot("CHANGE_INDICATOR", "MTOE", average=True)

    analysis.create_correlation_plot()
