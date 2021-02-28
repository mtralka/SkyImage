from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pandas as pd

from skyimage.stations import Sky
from skyimage.stations.Ground.GroundControl import GroundControl
from skyimage.utils.validators import validate_coords
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path
from skyimage.utils.validators import validate_modis_target_sublayers
from skyimage.utils.validators import validate_station_positions
from skyimage.utils.validators import validate_year


class SkyImage:
    """
    Control object for reconciling Sky and Ground objects


    Attributes
    ----------
    `year`: int
        Year to extract data for

    `j_day` : int or str
        Julian days to extract data for

    `station` : str
        Name of target station

    `station_positions` : Optional[dict]
        Optional override dict of all possible station positions

    `coords`: Optional[list or int]
        Spatial coordinates of `station`

    `modis_path` : str
        File path to MODIS station data

    `ground_path` : str
        File path to ground station data

    `modis_file_format` : Optional[str]
        File format of parent file to `target_sublayers`

    `modis_target_layers`: list
        Matching sublayers to each MODIS scene

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
        station_positions: Optional[dict] = None,
        coords: Optional[Union[list, int]] = None,
        modis_path: str = None,
        ground_path: str = None,
        modis_file_format: Optional[str] = "hdf",
        modis_target_sublayers: Optional[List] = None,
        save_images: Optional[bool] = False,
        show_images: Optional[bool] = False,
        show_time_stats: Optional[bool] = False,
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
        self.save_images: bool = save_images
        self.show_images: bool = show_images
        self.show_time_stats: bool = show_time_stats

    def run(self):

        self.Sky = Sky(
            j_day=self.j_days,
            year=self.year,
            path=self.modis_path,
            coords=self.coords,
            station=self.station_name,
        )

        matched_stds: dict = self.Sky.extract_stds()

        self.Ground = GroundControl(
            year=self.year,
            path=self.ground_path,
            coords=self.coords,
            station=self.station_name,
            stds=matched_stds,
            save_images=self.save_images,
            show_images=self.show_images,
        )

        self.Ground.run_all(show_time=self.show_time_stats)

    def results(
        self, as_dataframe: Optional[bool] = False, save_path: Optional[str] = ""
    ):

        if not hasattr(self, "Sky") or not hasattr(self, "Ground"):
            raise ValueError("Sky or Ground model uninitiated")

        sky_results: dict = self.Sky.results(as_dataframe=False)
        ground_results: dict = self.Ground.results(as_dataframe=False)

        if not as_dataframe:
            return {"SKY": sky_results, "GROUND": ground_results}

        sky_df = pd.DataFrame.from_dict(sky_results, orient="index").add_prefix("sky_")
        ground_df = pd.DataFrame.from_dict(ground_results, orient="index").add_prefix(
            "grnd_"
        )

        combined_df = pd.merge(sky_df, ground_df, left_index=True, right_index=True)

        if save_path:
            combined_df.to_csv(save_path)

        return combined_df
