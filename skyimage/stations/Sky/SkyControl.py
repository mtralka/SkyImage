from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pandas as pd
import rasterio as rio
from rich.progress import track
from skyimage.stations.Sky.SkyScene import SkyScene
from skyimage.stations.Sky.utils.utils import SkyPlatform
from skyimage.utils.utils import Station as StationObject
from skyimage.utils.utils import buffer_value
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path


class SkyControl:
    """
    Control object for interfacing with `GroundImage` objects

    Attributes
    ----------

    `j_day` : int or str
        Target Julian day

    `year` : int
            Target year

    `path` : str
        File path to Sky station data

    `station` : StationObject or str
        Target station object or station name

    `stds` : list of datetime
        Datetime objects to extract data for

    `file_format` : str
        Override default 'hdf' file format

    `target_platform` : str or `SkyPlatform`
        Target Sky platform. Default = "MODIS"

    Methods
    -------
    `instantiate_scene_objects()`
        Create matching `SkyScene` objects to `self` search parameters

    `run_all()`
        Run all found `SkyScene` objects

    `results()`
        Return results from all processed `SkyScene` objects

    @static_method
    `get_metadata()`
        Helper method to extract spatial file metadata

    """

    def __init__(
        self,
        j_day: Optional[Union[int, str, list]] = None,
        year: int = None,
        path: str = None,
        station: Union[StationObject, str] = None,
        stds: Optional[dict] = None,
        file_format: str = "hdf",
        target_platform: Union[SkyPlatform, str] = "MODIS",
    ):

        self.path: str = validate_file_path(path, "MODIS")

        if isinstance(station, StationObject):
            self.station = station
        elif isinstance(station, str):
            self.station = StationObject(name=station)
        else:
            raise ValueError("`station` must be a str or type Station")

        if isinstance(target_platform, SkyPlatform):
            self.platform = target_platform
        elif isinstance(target_platform, str):
            self.platform = SkyPlatform(platform=target_platform)
        else:
            raise ValueError("`target_platform` must be a str or type `SkyPlatform`")

        if j_day and year:
            # turn j_day + year into datetime objects
            _, self.stds = validate_datetime(j_day, year)

            stds_dict: dict = {}
            for std in self.stds:
                j_day = buffer_value(std.timetuple().tm_yday, 3)
                stds_dict[str(std.year) + j_day] = std

            self.stds = stds_dict

        elif stds:
            self.stds = stds
        else:
            raise ValueError("Must provide `j_day` and `year` or `stds`")

        self.file_format: str = file_format
        self.scenes: Dict[str, str] = self.__instantiate_scene_objects()

    def __str__(self):
        self_str: str = f"""
        Sky station
        --------
        Data Path : {self.path}
        File Format : {self.file_format}

        Window Target
        --------
        Station : {self.station.name}
        Coords : {self.station.coords}

        {len(self.scenes)} scene(s) found
        """
        for k, v in self.scenes.items():
            self_str = self_str + str(v)

        return self_str

    @property
    def j_days(self) -> List[str]:
        j_days: list = []
        for target in self.stds.values():
            j_day = target.timetuple().tm_yday
            j_days.append(buffer_value(j_day, 3))
        return j_days

    @property
    def j_days_full(self) -> List[str]:
        return list(self.stds.keys())

    @property
    def datetimes(self) -> List[datetime]:
        return list(self.stds.values())

    def __instantiate_scene_objects(self) -> Dict[str, SkyScene]:
        """Create matching `SkyScene` objects to `self` search parameters

        Uses
        ----------
        `self.path` : str
            Path to Sky directory

        `self.station` : StationObject
            object of target station

        `self.file_format` : str
            File format of target images

        `self.stds` : Dict[year+jday, datetime]
            Dictionary with datetime object values keyed
            by year + julian day

        Returns
        ----------
        `matching_scenes` : Dict[str, `SkyScene`]

        """
        matching_scenes: dict = {}
        for k, std in self.stds.items():

            scn_obj = SkyScene(
                sky_path=self.path,
                station=self.station,
                target_time=std,
                file_format=self.file_format,
            )

            matching_scenes[k] = scn_obj

        return matching_scenes

    def run_all(self, show_time: bool = False) -> None:
        """Run all found SkyScene objects

        Parameters
        ----------
        show_time : bool
            show time statistics

        """
        start = datetime.now()
        for sky_obj in track(self.scenes.values(), description="Sky Scenes"):

            if not isinstance(sky_obj, SkyScene):
                raise ValueError("Iterable must be type `SkyScene`")

            sky_obj.run_all(show_time=show_time)

        if show_time:
            print("SkyScene Done-", datetime.now() - start)

    def results(
        self, as_dataframe: Optional[bool] = False
    ) -> Union[dict, pd.DataFrame]:
        """Get processed results from all SkyScene objects

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

        for sky_obj in self.scenes.values():

            if not isinstance(sky_obj, SkyScene):
                raise ValueError("Iterable must be type `SkyScene`")

            name: str = sky_obj.j_day_full
            results: dict = sky_obj.results()
            all_results[name] = results

        if as_dataframe:
            return pd.DataFrame.from_dict(all_results, orient="index")

        return all_results

    def extract_stds(self) -> dict:
        """Get matched `datetime`s from all
         `SkyScene` objects

        Returns
        ----------
        Dict : [str : datetime object]
            results as Dict

        """

        stds: dict = {}

        # iterate through SkyImage objects
        # and extract aquisition_time datetime
        for k, v in self.scenes.items():
            stds[k] = v.actual_datetime

        return stds

    @staticmethod
    def get_metadata(target) -> Dict:
        """Returns metadata of `target` spatial data file

        Parameters
        ----------
        target : str
            path to `target` spatial data file

        Returns
        ----------
        Dict
            Dictionary of metadata.

        """
        with rio.open(target) as ds:
            meta = ds.meta
        return meta
