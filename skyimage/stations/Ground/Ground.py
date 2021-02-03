import glob
import logging
from typing import Dict
from typing import List

import numpy as np
import pandas as pd
from skyimage.utils.models import Stations
from skyimage.utils.validators import validate_coords
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path
from skyimage.utils.validators import validate_modis_target_sublayers
from skyimage.utils.validators import validate_station_positions


class Ground:
    """
    Object with data from the MODIS platform

    ...

    Attributes
    ----------
    path : str
        File path to platform data

    station_positions : dict
        Dict of all possible station positions

    station_name : str
        Name of target station

    coords: List of float
        Spatial coordinates of `station`

    j_day : list of str
        Julian days to extract data for

    stds : list of datetime
        Datetime objects to extract data for

    Methods
    -------
    results
        return process results

    """

    def __init__(
        self,
        j_day: int or str or list = None,
        year: int = None,
        path: str = None,
        coords: List[float] = None,
        station: str = None,
        station_positions: Stations = None,
    ):
   
        self.path: str = validate_file_path(path, "GROUND")
        self.station_positions: Stations = validate_station_positions(station_positions)
        self.station_name: str = station
        self.coords: List[float, float] = validate_coords(
            coords, station, self.station_positions
        )
        self.j_days, self.stds = validate_datetime(j_day, year)

        # self.scenes: Dict[str, str] = self.find_matching_scenes()
        # self.scenes_metadata: Dict[str, dict] = {
        #     k: self.get_metadata(v) for k, v in self.scenes.items()
        # }
        # self.scenes_sublayers: Dict[str, str] = {
        #     k: self.find_target_sublayers(v) for k, v in self.scenes.items()
        # }
        # self.raw_poi: Dict[str, Dict[str, object]] = {
        #     k: self.extract_poi_data(v) for k, v in self.scenes_sublayers.items()
        # }
        # self.poi: Dict[str, dict] = {
        #     k: self.process_poi_data(v) for k, v in self.raw_poi.items()
        # }

    def __str__(self):

    return f"""
    Ground platform
    --------
    Data Path : {self.path}
    File Format : {self.file_format}
    Target Sublayers : {self.target_sublayers}
    --------
    Station : {self.station_name}
    Coords : {self.coords}
    Year : {self.stds[0].year}
    Julian Days : {self.j_days[0]} - {self.j_days[-1]}

    {len(self.scenes)} scenes found

    INFO
    --------
    {self.poi}
    """
