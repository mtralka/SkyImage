from datetime import date
from datetime import datetime
from typing import List
from typing import Optional
from typing import Union

from matplotlib.pyplot import savefig
import pandas as pd

from skyimage.stations.Ground.GroundControl import GroundControl
from skyimage.stations.Sky.SkyControl import SkyControl
from skyimage.utils.utils import Station as StationObject
from skyimage.utils.utils import buffer_value
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path


class SkyImage:
    """
    Control object for orchestrating `SkyControl` and `GroundControl` objects


    Attributes
    ----------
    `year`: int
        Year to extract data for

    `j_day` : int or str
        Julian days to extract data for

    `station` : str
        Name of target station

    `sky_path` : str
        File path to sky station data

    `ground_path` : str
        File path to ground station data

    `save_images`: bool
        Boolean for saving photo and cloud mask results

    `show_images`: bool
        Boolean for showing photo and cloud mask results

    Methods
    -------
    `run()`
        Run all computations to specifications

    `results()`
        return process results

    """

    def __init__(
        self,
        year: int = None,
        j_day: Union[int, str] = None,
        station: str = None,
        sky_path: str = None,
        ground_path: str = None,
        save_images: Optional[bool] = False,
        show_images: Optional[bool] = False,
        show_time_stats: Optional[bool] = False,
    ):

        self.ground_path = validate_file_path(ground_path, "ground")
        self.modis_path = validate_file_path(sky_path, "MODIS")

        self.station = StationObject(name=station)

        # create datetime objects asap
        # app return j_day and j_day_full properties
        _, self.stds = validate_datetime(j_day, year)
        stds_dict: dict = {}
        for std in self.stds:
            j_day = buffer_value(std.timetuple().tm_yday, 3)
            stds_dict[str(std.year) + j_day] = std

        self.stds = stds_dict
        self.save_images: bool = save_images
        self.show_images: bool = show_images
        self.show_time_stats: bool = show_time_stats

    @property
    def j_days(self) -> List[str]:
        j_days: list = []
        for target in self.stds.values():
            j_day = target.timetuple().tm_yday
            j_days.append(buffer_value(j_day, 3))
        return j_days

    @property
    def j_days_full(self, abbrev: bool = False) -> List[str]:

        return list(self.stds.keys())

    @property
    def j_days_abrev(self) -> str:
        j_days: list = list(self.stds.keys())
        first: str = j_days[0]
        last: str = j_days[-1]

        return f"{first}-{last}"

    @property
    def datetimes(self) -> List[datetime]:
        return list(self.stds.values())

    def __str__(self) -> str:
        return f"""
        {self.sky}

        {self.ground}
        """

    def run(self):

        self.sky = SkyControl(
            stds=self.stds, path=self.modis_path, station=self.station
        )

        self.sky.run_all(show_time=self.show_time_stats)

        matched_stds: dict = self.sky.extract_stds()

        self.ground = GroundControl(
            path=self.ground_path,
            station=self.station,
            stds=matched_stds,
            save_images=self.save_images,
            show_images=self.show_images,
        )

        self.ground.run_all(show_time=self.show_time_stats)

    def results(self, as_dataframe: Optional[bool] = False, save: bool = False):

        if not hasattr(self, "sky"):
            raise AssertionError(
                "SkyControl object required, no SkyImage objects present"
            )

        if not hasattr(self, "ground"):
            raise AssertionError(
                "GroundControl object required, no GroundImage objects present"
            )

        if save and not as_dataframe:
            as_dataframe = True

        sky_results: dict = self.sky.results(as_dataframe=False)
        ground_results: dict = self.ground.results(as_dataframe=False)

        if not as_dataframe:
            return {"SKY": sky_results, "GROUND": ground_results}

        sky_df = pd.DataFrame.from_dict(sky_results, orient="index").add_prefix("sky_")
        ground_df = pd.DataFrame.from_dict(ground_results, orient="index").add_prefix(
            "grnd_"
        )

        combined_df = pd.merge(sky_df, ground_df, left_index=True, right_index=True)

        if save:
            combined_df.to_csv(f"SkyImage_Results_{self.j_days_abrev}.csv")

        return combined_df
