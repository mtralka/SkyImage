import datetime
import glob
import os
import re
import sys
from typing import Dict
from typing import List

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio

from skyimage import stations
from skyimage.stations import Ground
from skyimage.stations import Sky
from skyimage.utils.validators import validate_coords
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path
from skyimage.utils.validators import validate_modis_target_sublayers
from skyimage.utils.validators import validate_station_positions
from skyimage.utils.validators import validate_year


class SkyImage:
    def __init__(
        self,
        year: int = None,
        station: str = None,
        station_positions: Dict = None,
        coords: List or int = None,
        j_day: int or str = None,
        modis_path: str = None,
        ground_path: str = None,
        modis_file_format: str = "hdf",
        modis_target_sublayers: List = None,
    ):

        self.ground_path = validate_file_path(ground_path, "ground")
        self.modis_path = validate_file_path(modis_path, "MODIS")
        self.modis_target_layers = validate_modis_target_sublayers(
            modis_target_sublayers
        )
        self.station_positions = validate_station_positions(station_positions)
        self.station_name: str = station
        self.coords = validate_coords(coords, station, self.station_positions)
        self.j_days, self.stds = validate_datetime(j_day, year)
        self.year = validate_year(year)
        self.modis_file_format = modis_file_format

    def results(self, as_dataframe: bool = False):
        # if not self.Sky and self.Ground:
        #     raise Exception("Run Run")

        results: dict = {}

        if self.Sky:
            results | self.Sky.results(as_dataframe=False)
        if self.Ground:
            results | self.Ground.results()
        if as_dataframe:
            return pd.DataFrame.from_dict(results, orient="index")

        return {"SKY": self.Sky, "GROUND": "NULL"}

    def run(self):

        self.Sky = Sky(
            j_day=self.j_days,
            year=self.year,
            path=self.modis_path,
            coords=self.coords,
            station=self.station_name,
        )
        # self.Ground = Ground(self)
