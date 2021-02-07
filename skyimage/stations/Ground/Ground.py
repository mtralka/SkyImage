import glob
import logging
from typing import Dict
from typing import List
import warnings

from matplotlib.pyplot import show
import numpy as np
import pandas as pd
from skyimage.stations.Ground.utils.image import open_image
from skyimage.stations.Ground.utils.image import open_mask
from skyimage.stations.Ground.utils.image import show_image
#from skyimage.stations.Ground.utils.validators import validate_target_time
from skyimage.utils.models import Stations
from skyimage.utils.utils import buffer_value
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
        stds: dict = None,
        target_time: str = None,
    ):

        self.path: str = validate_file_path(path, "GROUND")
        self.station_positions: Stations = validate_station_positions(
            station_positions)
        self.station_name: str = station
        self.coords: List[float, float] = validate_coords(
            coords, station, self.station_positions
        )

        if j_day:
            if not target_time:
                warnings.warn("No `target_time` set, defaulting to 12:00",
                            UserWarning, stacklevel=2,)

                target_time = "12:00"

            self.j_days, self.stds = validate_datetime(j_day, year)
            hour, minute = target_time.split(":")

            for std in self.stds:
                std.replace(hour=int(hour), minute=int(minute))

        elif stds:
            self.stds = stds
        else:
            raise ValueError("Must provide j_day + year or stds")
        

        self.file_format: str = file_format
        self.target_time = target_time
        self.crop_mask = open_mask()
        self.images: Dict[str, str] = self.find_matching_images()
        self.raw_poi: Dict[str, Dict[str, object]] = {
            k: self.extract_poi_data(v) for k, v in self.images.items()
        }
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

    def find_matching_images(self) -> Dict:
        """Find images matching class variables

        Parameters
        ----------
        year : str
            Year of target scenes.

        stds : dict of str
            Dict of target datetimes

        path : str
            Path to image directory

        file_format : str
            File format of target scenes
    
        station_name : str
            Name of target station

        Returns
        ----------
        Dict
            [ year + Julian day : image file path]

        Raises
        ----------
        FileNotFoundError
            If no files match input paramters

        """

        path: str = self.path
        station_name: str = self.station_name
        file_format: str = self.file_format
        target_stds: dict = self.stds
        matching_images: dict = {}

        print("matching ", len(target_stds), " items")

        for k, std in target_stds.items():

            user_selection = 0

            year = str(std.year)
            month = buffer_value(std.month, 2)
            day = buffer_value(std.day, 2)
            #  j_day = buffer_value(std.timetuple().tm_yday, 3)
            hour = buffer_value(std.hour, 2)
            minute = buffer_value(std.minute, 2)

            matching_file_list = list(
                glob.iglob(path + f"/{station_name}/{year}/{month}/{day}/*{year + month + day}*{hour + minute}*.{file_format}")
            )

            if not matching_file_list:
                raise FileNotFoundError(f"GROUND image {year}-{day} not found")
            elif len(matching_file_list) > 1:
                #  for index, file in enumerate(matching_file_list):
                #     print(f"{index} | {file}") # TODO make this prettier and present time
                #  user_selection = int(input("Which file would you like?"))
                raise LookupError("Multiple matching files found")

            logging.info(f"GROUND scene {std} found")

            matching_images[std] = matching_file_list[user_selection]

        return matching_images

    def extract_poi_data(self, image_path: dict) -> dict:
        """Extract and process image from `image_path`.


        Parameters
        ----------
        image_path : dict
            [ std : path to image ]

        Returns
        ----------
        Dict
            [ std : windowed sublayer data ]

        """
        crop_mask = self.crop_mask
        img_arr = open_image(image_path)

        img = img_arr * crop_mask
        
        #show_image(img)
        img = img.astype('float')
        img[img == 0] = np.nan
        R = img[:, :, 0]
        G = img[:, :, 1]
        B = img[:, :, 2]

        R = R / 255
        B = B / 255
        G = G / 255

        SI = (B - R) / (B + R)
        SI = SI.flatten()
        SI = SI.astype('float')
        SI[SI == 0] = np.nan
        print("SI", np.nanmean(SI))

        BI = (R + G + B) / 3
        BI = BI.astype('float')
        BI[BI == 0] = np.nan
        print("BI", np.nanmean(BI))

        if not hasattr(self, 'BI'):
            print("checl")
            self.BI = BI.flatten()
            self.SI = SI.flatten()
        else:
            print(len(self.BI.flatten()))
            self.BI = np.hstack((self.BI, BI.flatten()))
            self.BI = self.BI.flatten()

            self.SI = np.hstack((self.SI, SI.flatten()))
            self.SI = self.SI.flatten()


        return img
