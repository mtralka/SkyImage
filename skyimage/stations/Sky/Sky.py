import glob
import logging
from typing import Dict
from typing import List

import numpy as np
import rasterio as rio
from skyimage import stations
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

    j_days : list of str
        Julian days to extract data for

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

    """
    def __init__(
        self,
        j_day: int or str or list = None,
        year: int = None,
        path: str = None,
        file_format: str = "hdf",
        coords: List[float] = None,
        station: str = None,
        station_positions: Stations = None,
        target_sublayers: List[str] = None,
    ):

        self.path: str = validate_file_path(path, "MODIS")
        self.target_sublayers: List[str] = validate_modis_target_sublayers(target_sublayers)
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

    def __decimal_to_binary(self, decimal: int or str) -> str:
        """Convert decimal to binary

        Parameters
        ----------
        decimal : int or str
            Decimal form.

        Returns
        ----------
        str
            Binary form.

        Examples
        ----------
        >>> __decimal_to_binary(59)
        111011
        >>> __decimal_to_binary("462")
        111001110
        """
        if type(decimal) is str:
            decimal = int(decimal)
        return str(bin(decimal))[2:]

    def __binary_to_decimal(self, binary: str) -> int:
        """Convert binary to decimal

        Parameters
        ----------
        binary : str
            Binary form.

        Returns
        ----------
        int
            Decimal form.

        Examples
        ----------
        >>> __binary_to_decimal(111001110)
        462
        >>> __decimal_to_binary(110001)
        49
        """
        return int(binary, 2)

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
                glob.iglob(path + f"/{year}/*{year + day}*.{file_format}")
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

    def get_metadata(self, target) -> Dict:
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
            """ Make abbreviation of str

            Join first letter of each word

            """
            return "".join([word[0] for word in target.split()]).upper()

        with rio.open(layer) as ds:
            crs = ds.read_crs()
            for name in ds.subdatasets:
                for target in target_sublayers:
                    if target in name:
                        logging.info(f"{target} layer found")
                        abbrev = __make_abbrev(target)
                        found_layers[abbrev] = name
        for target in target_sublayers:
            abbrev = __make_abbrev(target)
            if abbrev not in found_layers.keys():
                raise FileNotFoundError(f"Could not find {target} in sublayers. Check {layer}")
        return found_layers

    def extract_poi_data(self, sublayer_paths: Dict) -> Dict:
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
        # TODO add custom window
        lat = self.coords[0]
        lon = self.coords[1]
        poi_dict = {}

        for key, val in sublayer_paths.items():
            with rio.open(val) as ds:
                self.crs = ds.read_crs()
                py, px = ds.index(lon, lat)
                # window = rio.windows.Window(px - 1, py - 1, 3, 3)
                window = rio.windows.Window(px - 1, py - 1, 1, 1)
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
            If Coarse Resolution Granule Time (CRGT) not in `raw_data`

        KeyError
            If Coarse Resolution Number Mapping (CRNM) or n Pixel Amount (NPA) not in `raw_data`

        Notes
        ----------

        TODO add information about execution

        """

        def __find_percent(num, total=None) -> float:
            if not total:
                total = pixel_total
            return num / total

        processed_dict = {}

        if "CRGT" in raw_data.keys():
            processed_dict["time_utc"] = int(np.mean(raw_data["CRGT"]))
        else:
            raise KeyError(
                "Unable to assert MODIS scene aquisition time. Check CRGT sublayer "
            )

        if "CRNM" and "NPA" in raw_data.keys():

            NUM_MAPPINGS = {
                "CLD": "0-7",
                "CLD_SHDW": "8-15",
                "ADJ_CLD": "16-23",
                "SNW": "24-31",
            }

            pixel_total = raw_data["NPA"].sum()
            # processed_dict["n_pixel_total"] = n_pixel_total

            crnm = raw_data["CRNM"].flatten()

            cld, cld_shdw, adj_cld, snw = 0, 0, 0, 0
            for pixel in crnm:
                binary = self.__decimal_to_binary(str(pixel))
                # TODO binary solving for cover

            processed_dict["n_CLD"] = cld
            processed_dict["n_CLD_SHW"] = cld_shdw
            processed_dict["n_ADJ_CLD"] = adj_cld
            processed_dict["n_SNW"] = snw
            processed_dict["n_TOTAL"] = pixel_total

            processed_dict["prcnt_CLD"] = __find_percent(cld)
            processed_dict["prcnt_CLD_SHW"] = __find_percent(cld_shdw)
            processed_dict["prcnt_ADJ_CLD"] = __find_percent(adj_cld)
            processed_dict["prcnt_SNW"] = __find_percent(snw)
            
            # processed_dict["prcnt_cover"] = {
            #     "CLD": __find_percent(cld),
            #     "CLD_SHW": __find_percent(cld_shdw),
            #     "ADJ_CLD": __find_percent(adj_cld),
            #     "SNW": __find_percent(snw),
            # }
            # processed_dict["n_pixels"] = {
            #     "CLD": cld,
            #     "CLD_SHW": cld_shdw,
            #     "ADJ_CLD": adj_cld,
            #     "SNW": snw,
            #     "TOTAL": pixel_total,
            # }
        else:
            raise KeyError(
                "Unable to assert MODIS cloud cover. Check CRNM and NPA sublayers"
            )

        return processed_dict
