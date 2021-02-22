from datetime import datetime
import glob
import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import numpy as np
import pandas as pd
import rasterio as rio
from scipy import stats
from skyimage.stations.Sky.utils.utils import binary_to_decimal
from skyimage.stations.Sky.utils.utils import decimal_to_binary
from skyimage.utils.models import Stations
from skyimage.utils.validators import validate_coords
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path
from skyimage.utils.validators import validate_modis_target_sublayers
from skyimage.utils.validators import validate_station_positions


class Sky:
    """
    Object with data from the MODIS platform

    ...

    Attributes
    ----------
    path : str
        File path to platform data

    target_sublayers : list of str
        Targetted sublayers

    station_positions : dict
        Dict of all possible station positions

    station_name : str
        Name of target station

    coords: List of float
        Spatial coordinates of `station`

    j_day : list of str
        Julian days to extract data for

    year: int
        Year to extract data for

    stds : list of datetime
        Datetime objects to extract data for

    file_format : str
        File format of parent file to `target_sublayers`

    scenes : Dict[year + julian day , file path]
        File paths to scenes matching class paramters from `path`

    scenes_metadata : Dict[year + julian day : file metadata]
        Metadata of scenes matching class paramters from `path`

    scenes_sublayers : Dict[ year + julian day : Dict[ layer abbreviation : matching sublayers ]]
        Matching sublayers to each scene from `scenes`

    raw_poi : Dict[ year + julian day : Dict[ layer abbreviation : Numpy array ]]
        Extracted arrays for `target_sublayers` in all `scenes`

    poi : Dict [ year + julian day : dict ]
        Processed final product extracted from `raw_poi`

    Methods
    -------
    results
        return process results

    extract_std
        return datetime representing found scene(s) aquistion times

    """

    def __init__(
        self,
        j_day: Optional[Union[int, str, list]] = None,
        year: int = None,
        path: str = None,
        file_format: str = "hdf",
        coords: List[float] = None,
        station: str = None,
        station_positions: Stations = None,
        target_sublayers: List[str] = None,
    ):

        self.path: str = validate_file_path(path, "MODIS")
        self.target_sublayers: List[str] = validate_modis_target_sublayers(
            target_sublayers
        )
        self.station_positions: Stations = validate_station_positions(station_positions)
        self.station_name: str = station
        self.coords: List[float, float] = validate_coords(
            coords, station, self.station_positions
        )
        self.j_days, self.stds = validate_datetime(j_day, year)
        self.file_format: str = file_format

        self.scenes: Dict[str, str] = self.find_matching_scenes()
        self.scenes_metadata: Dict[str, dict] = {
            k: self.get_metadata(v) for k, v in self.scenes.items()
        }
        self.scenes_sublayers: Dict[str, str] = {
            k: self.find_target_sublayers(v) for k, v in self.scenes.items()
        }
        self.raw_poi: Dict[str, Dict[str, object]] = {
            k: self.extract_poi_data(v) for k, v in self.scenes_sublayers.items()
        }
        self.poi: Dict[str, dict] = {
            k: self.process_poi_data(v) for k, v in self.raw_poi.items()
        }

    def __str__(self):

        return f"""
        Sky platform
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

        year: str = str(self.stds[0].year)
        j_days: list = self.j_days
        path = self.path
        file_format = self.file_format
        matching_scenes: Dict = {}

        for day in j_days:
            user_selection = 0
            matching_file_list = list(
                glob.iglob(path + f"/{year}/*A{year + day}*.{file_format}")
            )

            if not matching_file_list:
                raise FileNotFoundError(f"MODIS scene {year}-{day} not found")
            elif len(matching_file_list) > 1:
                pass
                #  for index, file in enumerate(matching_file_list):
                #     print(f"{index} | {file}") # TODO make this prettier and present time
                #  user_selection = int(input("Which file would you like?"))
                #  raise LookupError("Multiple matching files found")
            else:
                logging.info(f"MODIS scene {year}-{day} found")

            matching_scenes[year + day] = matching_file_list[user_selection]

        return matching_scenes

    @staticmethod
    def get_metadata(target) -> Dict:
        """Returns metadata of `target`

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

    def find_target_sublayers(self, layer: str) -> Dict:
        """Finds file path to sublayers of `layer`

        Parameters
        ----------
        layer : str
            Path to target layer.

        target_sublayers : list of str
            List of desired sublayers.

        Returns
        ----------
        Dict
            [ sublayer abbreviation : path to sublayer ]

        Raises
        ----------
        FileNotFoundError
            If not all requested sublayers are present in target file

        """
        target_sublayers = self.target_sublayers
        found_layers = {}

        def __make_abbrev(name: str) -> str:
            """Make abbreviation of str

            Join first letter of each word

            """
            return "".join([word[0] for word in name.split()]).upper()

        with rio.open(layer) as ds:
            for name in ds.subdatasets:
                for target in target_sublayers:
                    if target in name:
                        logging.info(f"{target} layer found")
                        abbrev = __make_abbrev(target)
                        found_layers[abbrev] = name
        for target in target_sublayers:
            abbrev = __make_abbrev(target)
            if abbrev not in found_layers.keys():
                raise FileNotFoundError(
                    f"Could not find {target} in sublayers. Check {layer}"
                )
        return found_layers

    def extract_poi_data(self, sublayer_paths: dict) -> dict:
        """Extract windowed data array from `sublayer_paths`

        Parameters
        ----------
        sublayer_paths : dict
            [ sublayer abbreviation : path to sublayer ]

        lat : float
            Latitude of poi.

        lon : float
            Longitude of poi.

        Returns
        ----------
        Dict
            [ sublayer abbreviation : windowed sublayer data ]

        """
        # current window is 3X3 pixels
        # TODO add custom window
        lat = self.coords[0]
        lon = self.coords[1]
        poi_dict = {}

        for key, val in sublayer_paths.items():
            with rio.open(val) as ds:

                self.crs = ds.read_crs()
                py, px = ds.index(lon, lat)
                # WINDOW ADJUST
                # first is 3x3, next is 2X2, next 1
                #window = rio.windows.Window(px - 1, py - 1, 3, 3)
                window = rio.windows.Window(px, py - 1, 2, 2)
                #window = rio.windows.Window(px, py, 1, 1)
                arr = ds.read(1, window=window)
                logging.info(f"{key}\n{window}\n{arr}")
                poi_dict[key] = arr
        return poi_dict

    def process_poi_data(self, raw_data: Dict) -> Dict:
        """Processes usable information from `raw_data`

        Parameters
        ----------
        raw_data : dict
            [ sublayer abbreviation : Numpy matrix of extracted data ]

        Returns
        ----------
        Dict
            [ sublayer abbreviation : path to sublayer ]

        Raises
        ----------
        KeyError
            If `ESSENTIAL_SUBLAYERS` (default=CRGT, CRNM, NPA) not in `raw_data`

        Notes
        ----------

        TODO add information about execution

        """

        processed_dict: dict = {}
        ESSENTIAL_SUBLAYERS = ["CRGT", "CRNM", "NPA"]

        for sub_layer in ESSENTIAL_SUBLAYERS:
            if sub_layer not in raw_data.keys():
                raise KeyError(
                    "Unable to assert main MODIS statistics. \
                    Check {sub_layer} sublayer"
                )

        time_mode, _ = stats.mode(raw_data["CRGT"])
        processed_dict["time_utc"] = time_mode[0][0]

        NUM_MAPPINGS: Dict[str, str] = {
            "CLD": "0-7",
            "CLD_SHDW": "8-15",
            "ADJ_CLD": "16-23",
            "SNW": "24-31",
        }

        avg_pixel_total = raw_data["NPA"].sum()
        processed_dict["n_TOTAL"] = avg_pixel_total

        crnm = raw_data["CRNM"].flatten()

        for pixel in crnm:

            binary: str = decimal_to_binary(str(pixel))

            for k, v in NUM_MAPPINGS.items():

                start_bit, end_bit = [int(x) for x in v.split("-")]
                end_i = len(binary) - start_bit
                start_i = end_i - (end_bit - start_bit) - 1

                mapped_octet: str = binary[start_i:end_i:1]
                mapped_decimal: int = binary_to_decimal(mapped_octet)

                processed_dict[k] = mapped_decimal + processed_dict.get(k, 0)

        for k, v in NUM_MAPPINGS.items():

            n_present_pixels: int = processed_dict.get(k, 0)
            prcnt_of_total: float = round((n_present_pixels / avg_pixel_total) * 100, 2)

            processed_dict[f"prcnt_{k}"] = prcnt_of_total

        return processed_dict

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

    def extract_stds(self) -> dict:
        """Get datetime results

        Returns
        ----------
        Dict : [str : datetime object]
            results as Dict

        """

        poi: dict = self.poi
        stds: dict = self.stds
        matched_stds: dict = {}

        for k, v in poi.items():
            std_taken = datetime.strptime(k, "%Y%j")
            time_taken: str = str(v["time_utc"])
            for time in stds:
                if std_taken == time:
                    hour: int = int(time_taken[0:2])
                    minute: int = int(time_taken[2::])
                    matched_stds[k] = time.replace(hour=hour, minute=minute)

        return matched_stds
