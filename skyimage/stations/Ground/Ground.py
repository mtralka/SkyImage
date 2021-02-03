import glob
import logging
from typing import Dict
from typing import List

import numpy as np
import pandas as pd
from skyimage.stations.Ground.utils.validators import validate_target_time
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

    file_format : str
        File format of parent file to `target_sublayers`
    
    year: int
        Year to extract data for

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
        file_format: str = "jpg",
        station_positions: Stations = None,
        stds: Dict[str: object] = None,
        target_time: str = None,
    ):
   
        self.path: str = validate_file_path(path, "GROUND")
        self.station_positions: Stations = validate_station_positions(station_positions)
        self.station_name: str = station
        self.coords: List[float, float] = validate_coords(
            coords, station, self.station_positions
        )
        if j_day:
            self.j_days, self.stds = validate_datetime(j_day, year)
        elif stds:
            self.stds = stds
        else:
            raise ValueError("Must provide j_day + year or stds")

        self.file_format: str = file_format
        
        self.target_time = target_time
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


def find_matching_scenes(self) -> Dict:
    """Find scenes matching class variables

    Parameters
    ----------
    year : str
        Year of target scenes.

    j_days : list of str
        List of target Julian days

    path : str
        Path to scene directory

    file_format : str
        File format of target scenes

    Returns
    ----------
    Dict
        [ year + Julian day : layer file path]

    Raises
    ----------
    FileNotFoundError
        If no files match input paramters

    """

    path: str = self.path
    station_name: str = self.station_name
    file_format: str = self.file_format
    target_stds: dict = self.stds
    target_time: str = self.target_time
    matching_images: dict = {}

    for std in target_stds:
        
        user_selection = 0

        day = std.day
        month = std.month
        year = std.year
        j_day = std.timetuple().tm_yday
        
        if std.hour == "0":
            hour = target_time[0:2]
            pass
        # TODO continue 

        # path / station_name / year / month / day / time ()
        # GSFC_20200401T150502_SKY1
        matching_file_list = list(
            glob.iglob(path + f"/{station_name}/{year}/{month}/{day}/*{year + j_day}*{}*.{file_format}")
        )

        if not matching_file_list:
            raise FileNotFoundError(f"GROUND image {year}-{day} not found")
        elif len(matching_file_list) > 1:
            #  for index, file in enumerate(matching_file_list):
            #     print(f"{index} | {file}") # TODO make this prettier and present time
            #  user_selection = int(input("Which file would you like?"))
            raise LookupError("Multiple matching files found")
        
        logging.info(f"MODIS scene {year}-{day} found")

        matching_scenes[year + day] = matching_file_list[user_selection]

    return matching_scenes
