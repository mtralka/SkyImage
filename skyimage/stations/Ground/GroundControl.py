from datetime import datetime
from typing import Dict
from typing import Optional
from typing import Union
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.progress import track
from skyimage.stations.Ground.GroundImage import GroundImage
from skyimage.utils.utils import Station as StationObject
from skyimage.utils.utils import buffer_value
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path


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

    `station` : StationObject or str
        Target station object or station name

    `file_format` : str
        File format of Ground imagery

    `stds` : list of datetime
        Datetime objects to extract data for

    `target_time` : str
        Target time to find Ground imagery

    `file_format` : str
        Override default 'jpg' file format

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
        station: Union[StationObject, str] = None,
        stds: Optional[dict] = None,
        target_time: Optional[str] = None,
        file_format: str = "jpg",
        save_images: bool = False,
        show_images: bool = False,
    ):

        self.path: str = validate_file_path(path, "GROUND")

        if isinstance(station, StationObject):
            self.station = station
        elif isinstance(station, str):
            self.station = StationObject(name=station)
        else:
            raise ValueError("`station` must be a str or type Station")

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
        self.file_format = file_format
        self.save_images: bool = save_images
        self.show_images: bool = show_images
        self.images: Dict[str, GroundImage] = self.__instantiate_image_objects()

    def __str__(self):
        self_str: str = f"""
        Ground station
        --------
        Data Path : {self.path}
        File Format : {self.file_format}
        --------
        Station : {self.station.name}
        Coords : {self.station.coords}

        {len(self.images)} scene(s) found
        """
        for k, v in self.images.items():
            self_str = self_str + str(v)

        return self_str

    def __instantiate_image_objects(self) -> Dict[str, GroundImage]:
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
        `matching_images` : Dict[str, `GroundImage`]

        """
        matching_images: Dict[str, StationObject] = {}
        for k, std in self.stds.items():

            found_image = GroundImage(
                ground_path=self.path,
                station=self.station,
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
