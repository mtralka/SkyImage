from collections import namedtuple
import glob
from itertools import product
import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from skyimage.stations.Ground.utils.image import calc_BI
from skyimage.stations.Ground.utils.image import calc_SI
from skyimage.stations.Ground.utils.image import extract_color_bands
from skyimage.stations.Ground.utils.image import extract_stats
from skyimage.stations.Ground.utils.image import f_above_or_below
from skyimage.stations.Ground.utils.image import open_image
from skyimage.stations.Ground.utils.image import open_mask
from skyimage.stations.Ground.utils.image import save_image
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
    
    save_images: bool
        Boolean for saving photo and cloud mask results

    show_images: bool
        Boolean for showing photo and cloud mask results

    Methods
    -------
    results
        return process results

    """

    def __init__(
        self,
        j_day: Union[int, str, list] = None,
        year: int = None,
        path: str = None,
        coords: Optional[List[float]] = None,
        station: Optional[str] = None,
        file_format: Optional[str] = "jpg",
        station_positions: Stations = None,
        stds: Optional[dict] = None,
        target_time: Optional[str] = None,
        save_images: Optional[bool] = None,
        show_images: Optional[bool] = None,
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

            stds_dict = {}

            for std in self.stds:
                j_day = buffer_value(std.timetuple().tm_yday, 3)
                stds_dict[str(std.year) + j_day] = std.replace(
                    hour=int(hour), minute=int(minute))

            self.stds = stds_dict

        elif stds:
            self.stds = stds
            self.j_days = []

            for j_day in self.stds.keys():
                self.j_days.append(j_day[-3:])

        else:
            raise ValueError("Must provide j_day + year or stds")

        self.crop_mask = open_mask()
        self.file_format: str = file_format
        self.target_time = target_time
        self.save_images: bool = save_images
        self.show_images: bool = show_images
        self.images: Dict[str, str] = self.find_matching_images()
        self.raw_poi: Dict[str, Dict[str, object]] = {
            k: self.extract_poi_data(k, v) for k, v in self.images.items()
        }
        self.poi: Dict[str, dict] = {
            k: self.process_poi_data(k, v) for k, v in self.raw_poi.items()
        }

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
                raise FileNotFoundError(f"GROUND image {year}-{month}-{day}-{hour}:{minute} not found")
                # TODO implement match closest
            elif len(matching_file_list) > 1:
                # TODO present use selection
                #  for index, file in enumerate(matching_file_list):
                #     print(f"{index} | {file}") 
                #  user_selection = int(input("Which file would you like?"))
                raise LookupError("Multiple matching files found")

            logging.info(f"GROUND scene {std} found")

            matching_images[k] = matching_file_list[user_selection]

        return matching_images

    def extract_poi_data(self, image_name: str, image_path: str) -> dict:
        """Extract `BI` and `SI` for image at `image_path`.

        Parameters
        ----------
        image_path : str
            path to image `C:\\path\\to\\image`

        Returns
        ----------
        Dict
            [ BI : BI_array, SI : SI_array ]

        """

        crop_mask = self.crop_mask

        img_arr = open_image(image_path)

        img = img_arr * crop_mask

        if self.show_images:
            show_image(img)

        if self.save_images:
            img_file_name = image_name + ".png"
            save_image(img_file_name, img.astype("uint8"))

        img = img.astype("float")
        img[img == 0] = np.nan

        R, G, B = extract_color_bands(img)

        SI = calc_SI(R, B)
        BI = calc_BI(R, G, B)

        return {"BI": BI, "SI": SI}

    def process_poi_data(self, image_name: str, raw_data: dict) -> dict:
        """Process image

        Parameters
        ----------
        raw_data : Dict[ BI : BI_array, SI : SI_array ]
            Dict containing `BI` and `SI` statistics
            as extracted with `extract_poi_data()`

        Returns
        ----------
        Dict: [ BI : BI_stats, SI : SI_stats ]
            Dict with statistics


        """

        BI = raw_data["BI"]
        SI = raw_data["SI"]

        # we keep NaNs to preserve image shape
        # for reconstitution after cloud mask creation
        # BI = BI[np.logical_not(np.isnan(BI))]
        # SI = SI[np.logical_not(np.isnan(SI))]

        BI_stats: dict = extract_stats(BI)
        SI_stats: dict = extract_stats(SI)
        BI_SI_points = np.column_stack((BI.flatten(), SI.flatten()))

        x_step = [0, .1, .35, .7, .8, 1]
        y_step = [1, .6, .35, .15, .1, 0]
        boundary = np.column_stack((x_step, y_step))

        pixel_total: int = BI_SI_points[np.logical_not(
            np.isnan(BI_SI_points))].size / 2

        cloud_mask: list = []
        img_shape: tuple = BI.shape[0:2]
        number_clear: int = 0

        for point in BI_SI_points:
            results: int = f_above_or_below(point, boundary)
            cloud_mask.append(results)
            number_clear = number_clear + results

        cloud_mask = np.array(cloud_mask).reshape(img_shape)

        if self.show_images:
            show_image(cloud_mask)

        if self.save_images:
            img_file_name = image_name + "_cld_mask.png"
            save_image(img_file_name, cloud_mask)

        percent_cloud: float = round(
            ((pixel_total - number_clear) / pixel_total) * 100, 2)

        return {"BI": BI_stats, "SI": SI_stats,
                "n_TOTAL": pixel_total, "prcnt_CLD": percent_cloud}

    def results(self, as_dataframe: Optional[bool] = True):
        """Get processed results

        Parameters
        ----------
        as_dataframe : bool
            return as pandas dataframe

        Returns
        ----------
        Dict : dict
            results as Dict

        """

        if as_dataframe:
            return pd.DataFrame.from_dict(self.poi, orient="index")

        return self.poi

    @staticmethod
    def show_graph(poi: dict = None, BI=None, SI=None, save: Optional[bool] = None, file_name: Optional[str]= None):

        if poi:
            BI = poi["BI"]
            SI = poi["SI"]
        elif not BI and not SI:
            raise TypeError("Require poi Dict ['BI' : array, 'SI': array ] or BI / SI") 

        BI = BI.flatten()
        SI = SI.flatten()

        x = BI[np.logical_not(np.isnan(BI))]
        y = SI[np.logical_not(np.isnan(SI))]

        plt.xlabel("BI")
        plt.ylabel("SI")

        plt.hist2d(x, y, (50, 50), cmap=plt.cm.jet)

        x_step = [0, .1, .35, .7, .8, 1]
        y_step = [1, .6, .35, .15, .1, 0]
        plt.plot(x_step, y_step, "w")

        plt.colorbar()

        if save:
            plt.savefig(file_name, dpi=100)

        plt.clf()
