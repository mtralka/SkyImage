import datetime
import glob
import os
import re
import sys
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

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
        coords: Optional[Union[list, int]] = None,
        j_day: Union[int, str] = None,
        modis_path: str = None,
        ground_path: str = None,
        modis_file_format: Optional[str] = "hdf",
        modis_target_sublayers: Optional[List] = None,
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

        results: dict = {}

        if self.Sky:
            sky_results = self.Sky.results(as_dataframe=False)
            results = {**results, **sky_results}
        if self.Ground:
            ground_results = self.Ground.results(as_dataframe=False)
            results = {**results, **ground_results}

        if as_dataframe:
            return pd.DataFrame.from_dict(results, orient="index")

        return {"SKY": sky_results, "GROUND": ground_results}

    def run(self):

        self.Sky = Sky(
            j_day=self.j_days,
            year=self.year,
            path=self.modis_path,
            coords=self.coords,
            station=self.station_name,
        )

        matched_stds: dict = self.Sky.extract_stds()

        self.Ground = Ground(
            year=self.year,
            path=self.ground_path,
            coords=self.coords,
            station=self.station_name,
            stds=matched_stds,
        )
        # self.Ground = Ground(self)
