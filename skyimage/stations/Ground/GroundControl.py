from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.progress import track
from skyimage.stations.Ground.GroundImage import GroundImage
from skyimage.utils.models import Stations
from skyimage.utils.utils import Station
from skyimage.utils.utils import buffer_value
from skyimage.utils.validators import validate_coords
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path
from skyimage.utils.validators import validate_station_positions


class GroundControl:
    """
    Control object for interfacing with `GroundImage` objects

    Attributes
    ----------

    `j_day` : int or str
        Target Julian day

    `year` : int
            Target year

    `path` : str
        File path to Ground station data

    `coords` : List of float
        Spatial coordinates of `station_name`

    `station` : str
        Target station name

    `file_format` : str
        File format of Ground imagery

    `station_positions`: dict
        Dict overridding all possible station positions

    `stds` : list of datetime
        Datetime objects to extract data for

    `target_time` : str
        Target time to find Ground imagery

    `save_images`: bool
        Boolean for saving photo and cloud mask results

    `show_images`: bool
        Boolean for showing photo and cloud mask results

    Methods
    -------
    `instantiate_image_objects()`
        Create matching `GroundImage` objects to `self` search parameters

    `run_all()`
        Run all found `GroundImage` objects

    `results()`
        Return results from all processed `GroundImage` objects

    @static_method
    `show_graph()`
        Helper method to chart BI / SI values

    """

    def __init__(
        self,
        j_day: Union[int, str, list] = None,
        year: int = None,
        path: str = None,
        coords: Optional[List[float]] = None,
        station: Optional[str] = None,
        station_positions: Stations = None,
        stds: Optional[dict] = None,
        target_time: Optional[str] = None,
        save_images: bool = False,
        show_images: bool = False,
    ):

        self.path: str = validate_file_path(path, "GROUND")
        self.station_positions: Stations = validate_station_positions(station_positions)
        self.station_name: str = station
        self.coords: List[float, float] = validate_coords(
            coords, station, self.station_positions
        )

        if j_day:
            if not target_time:
                warnings.warn(
                    "No `target_time` set, defaulting to 12:00",
                    UserWarning,
                    stacklevel=2,
                )

                target_time = "12:00"

            self.j_days, self.stds = validate_datetime(j_day, year)
            hour, minute = target_time.split(":")

            stds_dict = {}

            for std in self.stds:
                j_day = buffer_value(std.timetuple().tm_yday, 3)
                stds_dict[str(std.year) + j_day] = std.replace(
                    hour=int(hour), minute=int(minute)
                )

            self.stds = stds_dict

        elif stds:
            self.stds = stds
            self.j_days = []

            for j_day in self.stds.keys():
                self.j_days.append(j_day[-3:])

        else:
            raise ValueError("Must provide `j_day` and `year` or `stds`")

        self.target_time = target_time
        self.save_images: bool = save_images
        self.show_images: bool = show_images
        self.images: Dict[str, GroundImage] = self.instantiate_image_objects()

    def __str__(self):

        return f"""
        Ground station
        --------
        Data Path : {self.path}
        File Format : {self.file_format}
        --------
        Station : {self.station_name}
        Coords : {self.coords}

        {len(self.images)} scene(s) found
        """

    def instantiate_image_objects(self) -> Dict[str, GroundImage]:
        """Create matching `GroundImage` objects to `self` search parameters

        Uses
        ----------
        `self.path` : str
            Path to Ground directory

        `self.station_name` : str
            Name of target station

        `self.file_format` : str
            File format of target images

        `self.stds` : Dict[year+jday, datetime]
            Dictionary with datetime object values keyed
            by year + julian day

        Returns
        ----------
        `matching_images` : Dict[year + julian day , `GroundImage`]

        """
        matching_images: dict = {}
        for k, std in self.stds.items():

            found_image = GroundImage(
                ground_path=self.path,
                station=self.station_name,
                target_time=std
            )

            matching_images[k] = found_image

        return matching_images

    def run_all(self, show_time: bool = False) -> None:
        """Run all found GroundImage objects

        Parameters
        ----------
        show_time : bool
            show time statistics

        """
        start = datetime.now()
        for ground_obj in track(self.images.values(), description="Ground Images"):

            if not isinstance(ground_obj, GroundImage):
                raise ValueError("Iterable must be type `GroundImage`")

            ground_obj.run_all(show_time=show_time)

        if show_time:
            print("DONE-", datetime.now() - start)

    def results(self, as_dataframe: Optional[bool] = True) -> Union[dict, pd.DataFrame]:
        """Get processed results from all GroundImage objects

        Parameters
        ----------
        as_dataframe : bool
            return as pandas dataframe

        Returns
        ----------
        Dict : dict
            all results as Dict

        """
        all_results: dict = {}

        for ground_obj in self.images.values():

            if not isinstance(ground_obj, GroundImage):
                raise ValueError("Iterable must be type `GroundImage`")

            name = ground_obj.j_day_full
            results = ground_obj.results()
            all_results[name] = results

        if as_dataframe:
            return pd.DataFrame.from_dict(ground_obj, orient="index")

        return all_results

    @staticmethod
    def show_graph(
        poi: dict = None,
        BI=None,
        SI=None,
        save: Optional[bool] = None,
        file_name: Optional[str] = None,
    ):

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

        x_step = [0, 0.1, 0.35, 0.7, 0.8, 1]
        y_step = [1, 0.6, 0.35, 0.15, 0.1, 0]
        plt.plot(x_step, y_step, "w")

        cb = plt.colorbar()

        if save:
            plt.savefig(file_name, dpi=100)
            # TODO fix
            # one of these works
            cb.remove()
            plt.close()
            plt.close("all")
            plt.clf()
            plt.cla()
