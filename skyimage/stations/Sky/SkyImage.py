from datetime import datetime
import glob
import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
import warnings

from numpy import ndarray
import pandas as pd
import rasterio as rio
from scipy import stats
from skyimage.stations.Sky.utils.utils import TargetSublayers
from skyimage.stations.Sky.utils.utils import binary_to_decimal
from skyimage.stations.Sky.utils.utils import decimal_to_binary
from skyimage.utils.utils import Station as StationObject
from skyimage.utils.utils import buffer_value


class SkyImage:
    def __init__(
        self,
        direct_path: Optional[str] = None,
        target_date: datetime = None,
        station: Union[StationObject, str] = None,
        sky_path: str = None,
        file_format: str = "hdf",
    ):

        self.target_date: datetime = target_date
        self.direct_path: str = direct_path
        self.file_format = file_format

        if direct_path and sky_path:
            warnings.warn(
                "Both `sky_path and `direct_path` passed,\
                defaulting to `direct_path`",
                UserWarning,
                stacklevel=2,
            )

            self.direct_path = direct_path
        elif not direct_path:

            assert sky_path, "`sky_path` required when not using `direct_path`"
            assert target_date, "`target_date` required when not using `direct_path`"

            self.__find_matching_scene(target_date, sky_path)

        if isinstance(station, StationObject):
            self.station = station
        elif isinstance(station, str):
            self.station = StationObject(name=station)
        else:
            raise ValueError("`station` must be a str or type Station")

        self.target_sublayers: List[str] = TargetSublayers(platform="MODIS")
        self.processed: bool = False

        self.sub_layers: list
        self.raw_data: dict
        self.data: dict

    @property
    def j_day(self) -> str:
        j_day: int = self.target_date.timetuple().tm_yday
        return buffer_value(j_day, 3)

    @property
    def j_day_full(self) -> str:
        j_day: int = self.target_date.timetuple().tm_yday
        year: int = self.target_date.year
        return str(year) + buffer_value(j_day, 3)

    @property
    def name(self) -> str:
        date: str = self.j_day_full
        time: str = str(self.actual_time.strftime("%H:%M"))
        return f"{date}-{time}"

    def __str__(self) -> str:
        self_str: str = \
            f"""
            {self.name}
            {self.time_delta} second(s) from target
            """

        if self.processed:
            self_str = self_str + \
                f"""
                {self.prcnt_cld} % cloudy
                {self.n_total} total pixels
                BI
                {self.BI_stats}
                SI
                {self.SI_stats}
                """
        return self_str

    def __repr__(self) -> str:
        return f"<SkyImage {self.name}>"

    def __find_matching_scene(
        self, target_date: datetime, path: str
    ) -> None:
        """ Find path to desired scene

            Uses
            ----------

            `self.file_format` : str
                File format of target image

            Parameters
            ----------

            `target_date` : datetime
                target date of image

            `path` : str
                Path for image search

            Defines
            ----------
            `self.direct_path`
                path to target scene

            """
        year: str = str(target_date.year)
        j_day: str = self.j_day
        file_format = self.file_format

        matching_file_list = list(
            glob.iglob(path + f"/{year}/*A{year + j_day}*.{file_format}")
        )

        if not matching_file_list:
            raise FileNotFoundError(f"Ground scene {str(target_date)} not found")
        elif len(matching_file_list) > 1:
            raise LookupError(f"Multiple matching files found for {str(target_date)}")
        else:
            logging.info(f"Ground scene {str(target_date)} found")

        self.direct_path = matching_file_list[0]

    def run_all(
        self,
        show_time: bool = False,
    ) -> None:
        """ Run all class methods

        Parameters
        ----------
        show_time : bool
            show time statistics

        """
        # TODO
        start_time: datetime = datetime.now()
        self.extract()
        self.process()

        if show_time:
            print(self.name + "-", datetime.now() - start_time)

    def extract_sublayers(self) -> None:
        """ Extract sublayers from `self.direct_path`

            Uses
            ----------

            `self.direct_path` : str
                direct path to target scene

            `self.target_sublayers` : TargetSublayers
                target scene layers

            Defines
            ----------
            `self.direct_path`
                path to target image

            """
        found_layers = {}

        with rio.open(self.direct_path) as ds:
            for name in ds.subdatasets:
                for target in self.target_sublayers.layers:
                    if target in name:
                        logging.info(f"{target} layer found")
                        abbrev = TargetSublayers.make_abbreviation(target)
                        found_layers[abbrev] = name

        for target in self.target_sublayers.layers:
            abbrev = TargetSublayers.make_abbreviation(target)
            if abbrev not in found_layers.keys():
                raise FileNotFoundError(
                    f"Could not find {target} in sublayers. Check {self.direct_path}"
                )
        self.sub_layers = found_layers

    def extract(self) -> None:
        """Extract windowed data array `self.raw_data` from `sublayer_paths`

        Uses
        ----------

        `self.station` : Station
            Target `Station` object

        `self.sub_layers` : list
            found target sub layers

        Defines
        ----------
        `self.raw_data` : dict
            Dict of raw data values

        """
        # current window is 3X3 pixels
        # TODO add custom window
        lat = self.station.latitude
        lon = self.station.longitude
        poi_dict = {}

        for key, val in self.sub_layers.items():
            with rio.open(val) as ds:

                self.crs = ds.read_crs()
                py, px = ds.index(lon, lat)
                # WINDOW ADJUST
                # first is 3x3, next is 2X2, next 1
                # window = rio.windows.Window(px - 1, py - 1, 3, 3)
                window = rio.windows.Window(px, py - 1, 2, 2)
                # window = rio.windows.Window(px, py, 1, 1)
                arr = ds.read(1, window=window)
                logging.info(f"{key}\n{window}\n{arr}")
                poi_dict[key] = arr

        self.raw_data: dict = poi_dict

    def process(self) -> None:
        """ Process `self.raw_data` 

        Uses
        ----------
        `self.target_sublayers` : `TargetSublayers`
            Platform sublayer object

        `self.raw_data` : dict
            Dict of raw data values

        Defines
        ----------
        `self.data` : dict
            Processed information
            concerning image

        """

        processed_dict: dict = {}
        num_mappings: Dict[str] = self.target_sublayers.num_map

        for sub_layer in self.target_sublayers.essential:
            if sub_layer not in self.raw_data.keys():
                raise KeyError(
                    f"Unable to assert main {self.target_sublayers.name} statistics. \
                    Check {sub_layer} sublayer"
                )

        time_mode, _ = stats.mode(self.raw_data["CRGT"])
        processed_dict["time_utc"] = time_mode[0][0]

        avg_pixel_total = self.raw_data["NPA"].sum()
        processed_dict["n_TOTAL"] = avg_pixel_total

        crnm = self.raw_data["CRNM"].flatten()

        for pixel in crnm:

            binary: str = decimal_to_binary(str(pixel))

            for k, v in num_mappings.items():

                start_bit, end_bit = [int(x) for x in v.split("-")]
                end_i = len(binary) - start_bit
                start_i = end_i - (end_bit - start_bit) - 1

                mapped_octet: str = binary[start_i:end_i:1]
                mapped_decimal: int = binary_to_decimal(mapped_octet)

                processed_dict[k] = mapped_decimal + processed_dict.get(k, 0)

        for k, v in num_mappings.items():

            n_present_pixels: int = processed_dict.get(k, 0)
            prcnt_of_total: float = round((n_present_pixels / avg_pixel_total) * 100, 2)

            processed_dict[f"prcnt_{k}"] = prcnt_of_total

        self.processed: bool = True
        self.data: dict = processed_dict

    def results(self, as_dataframe: bool = False) -> Union[dict, pd.DataFrame]:

        results: dict = {self.j_day_full: self.data}

        if not self.processed:
            raise AssertionError("Object not processed")

        if as_dataframe:
            return pd.DataFrame.from_dict(results, orient="index")

        return results
